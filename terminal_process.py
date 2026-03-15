"""PTY + shell process management for SOSterm."""

import os
import select
import signal
from PyQt5.QtCore import QObject, QThread, pyqtSignal
import ptyprocess


class PtyReaderThread(QThread):
    """QThread that reads from PTY and emits batched data.

    Uses os.read() directly with a drain loop to coalesce many small
    kernel PTY reads into fewer, larger emissions.  This is critical for
    high-throughput output (e.g. Claude Code) where ptyprocess.read()
    returns ~54 bytes per call, flooding the Qt event loop with thousands
    of cross-thread signal deliveries.
    """

    data_received = pyqtSignal(bytes)
    finished_with_status = pyqtSignal(int)

    _READ_SIZE = 65536   # max bytes per os.read()

    def __init__(self, pty, parent=None):
        super().__init__(parent)
        self._pty = pty
        self._running = True

    def run(self):
        fd = self._pty.fd
        read_size = self._READ_SIZE
        try:
            while self._running and self._pty.isalive():
                try:
                    # Block until data is available (100ms timeout so we
                    # can check _running / isalive periodically).
                    ready, _, _ = select.select([fd], [], [], 0.1)
                    if not ready:
                        continue

                    # First read — guaranteed to return data since select said ready.
                    try:
                        buf = os.read(fd, read_size)
                    except OSError:
                        break
                    if not buf:
                        break  # EOF

                    # Drain loop: keep reading while more data is immediately
                    # available.  This coalesces the many tiny PTY reads into
                    # one large emission, reducing cross-thread signal overhead
                    # by ~100-200x during rapid output.
                    while True:
                        r, _, _ = select.select([fd], [], [], 0)
                        if not r:
                            break
                        try:
                            chunk = os.read(fd, read_size)
                        except OSError:
                            break
                        if not chunk:
                            break
                        buf += chunk

                    self.data_received.emit(buf)

                except EOFError:
                    break
                except OSError:
                    break
        finally:
            exit_status = -1
            try:
                exit_status = self._pty.wait()
            except Exception:
                pass
            self.finished_with_status.emit(exit_status)

    def stop(self):
        self._running = False


class TerminalProcess(QObject):
    """Manages a shell process running inside a PTY."""

    data_ready = pyqtSignal(bytes)
    process_exited = pyqtSignal(int)  # exit status

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pty = None
        self._reader = None
        self._running = False

    def start(self, shell="/bin/bash", rows=24, cols=80, cwd=None, colorfgbg=None,
              command=None):
        """Spawn a shell (or arbitrary command) in a new PTY.

        If *command* is provided (a list of strings), it is spawned directly
        instead of the shell.  This is used for SSH sessions.
        """
        env = dict(os.environ)
        env["TERM"] = "xterm-256color"
        env["COLORTERM"] = "truecolor"
        env.setdefault("LANG", "en_US.UTF-8")
        if colorfgbg:
            env["COLORFGBG"] = colorfgbg
        # Remove parent session markers so tools like Claude Code don't
        # refuse to run, thinking they are nested inside themselves.
        env.pop("CLAUDECODE", None)

        if cwd and os.path.isdir(cwd):
            env["PWD"] = cwd

        argv = command if command else [shell]

        self._pty = ptyprocess.PtyProcess.spawn(
            argv,
            dimensions=(rows, cols),
            env=env,
            cwd=cwd,
        )
        self._running = True

        self._reader = PtyReaderThread(self._pty, self)
        self._reader.data_received.connect(self.data_ready)
        self._reader.finished_with_status.connect(self._on_finished)
        self._reader.start()

    def _on_finished(self, status):
        self._running = False
        self.process_exited.emit(status)

    def write(self, data):
        """Write data to the PTY (send to shell)."""
        if self._pty and self._running:
            try:
                self._pty.write(data)
            except (OSError, EOFError):
                pass

    def resize(self, rows, cols):
        """Resize the PTY (sends SIGWINCH to child)."""
        if self._pty and self._running:
            try:
                self._pty.setwinsize(rows, cols)
            except (OSError, EOFError):
                pass

    def get_cwd(self):
        """Get the current working directory of the shell process."""
        if self._pty and self._running:
            try:
                pid = self._pty.pid
                cwd = os.readlink(f"/proc/{pid}/cwd")
                return cwd
            except (OSError, ProcessLookupError):
                pass
        return os.path.expanduser("~")

    def is_alive(self):
        """Check if the process is still running."""
        return self._running and self._pty is not None and self._pty.isalive()

    def terminate(self):
        """Terminate the shell process."""
        self._running = False
        if self._reader:
            self._reader.stop()
            self._reader.wait(2000)
            self._reader = None
        if self._pty:
            try:
                self._pty.kill(signal.SIGHUP)
            except (OSError, ProcessLookupError):
                pass
            try:
                self._pty.close()
            except Exception:
                pass
            self._pty = None
