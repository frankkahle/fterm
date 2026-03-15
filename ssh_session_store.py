"""SSH session data persistence for SOSterm."""

import configparser
import glob
import json
import os
import re
import uuid
from dataclasses import dataclass, field, asdict
from typing import List, Optional


@dataclass
class SSHGroup:
    id: str = ""
    name: str = ""
    color: str = ""
    expanded: bool = True

    def __post_init__(self):
        if not self.id:
            self.id = f"g-{uuid.uuid4().hex[:12]}"


@dataclass
class SSHSession:
    id: str = ""
    group_id: str = ""
    name: str = ""
    host: str = ""
    port: int = 22
    username: str = ""
    auth_method: str = "key"  # "key" or "password"
    identity_file: str = ""
    startup_command: str = ""
    color: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"s-{uuid.uuid4().hex[:12]}"

    def display_name(self) -> str:
        if self.name:
            return self.name
        label = ""
        if self.username:
            label += f"{self.username}@"
        label += self.host
        if self.port and self.port != 22:
            label += f":{self.port}"
        return label

    def build_command(self, default_identity_file="") -> list:
        cmd = ["ssh"]
        if self.port and self.port != 22:
            cmd += ["-p", str(self.port)]
        # Use session-specific key, or fall back to the global default
        identity = self.identity_file if self.identity_file else default_identity_file
        if identity:
            cmd += ["-i", os.path.expanduser(identity)]
        target = ""
        if self.username:
            target = f"{self.username}@{self.host}"
        else:
            target = self.host
        cmd.append(target)
        if self.startup_command:
            cmd.append(self.startup_command)
        return cmd


_CONFIG_DIR = os.path.expanduser("~/.config/SOSterm")
_SESSIONS_FILE = os.path.join(_CONFIG_DIR, "ssh_sessions.json")


class SSHSessionStore:
    """Load/save SSH sessions and groups from JSON."""

    def __init__(self, path=None):
        self._path = path or _SESSIONS_FILE
        self._groups: List[SSHGroup] = []
        self._sessions: List[SSHSession] = []
        self.load()

    # --- Persistence ---

    def load(self):
        if not os.path.exists(self._path):
            self._groups = []
            self._sessions = []
            return
        try:
            with open(self._path, "r") as f:
                data = json.load(f)
            self._groups = [SSHGroup(**g) for g in data.get("groups", [])]
            self._sessions = [SSHSession(**s) for s in data.get("sessions", [])]
        except (json.JSONDecodeError, TypeError, KeyError):
            self._groups = []
            self._sessions = []

    def save(self):
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        data = {
            "version": 1,
            "groups": [asdict(g) for g in self._groups],
            "sessions": [asdict(s) for s in self._sessions],
        }
        with open(self._path, "w") as f:
            json.dump(data, f, indent=2)

    # --- Group CRUD ---

    def groups(self) -> List[SSHGroup]:
        return list(self._groups)

    def get_group(self, group_id: str) -> Optional[SSHGroup]:
        for g in self._groups:
            if g.id == group_id:
                return g
        return None

    def add_group(self, group: SSHGroup):
        self._groups.append(group)
        self.save()

    def update_group(self, group: SSHGroup):
        for i, g in enumerate(self._groups):
            if g.id == group.id:
                self._groups[i] = group
                self.save()
                return
        self.add_group(group)

    def delete_group(self, group_id: str):
        self._groups = [g for g in self._groups if g.id != group_id]
        # Move sessions in this group to ungrouped
        for s in self._sessions:
            if s.group_id == group_id:
                s.group_id = ""
        self.save()

    # --- Session CRUD ---

    def sessions(self) -> List[SSHSession]:
        return list(self._sessions)

    def get_session(self, session_id: str) -> Optional[SSHSession]:
        for s in self._sessions:
            if s.id == session_id:
                return s
        return None

    def sessions_in_group(self, group_id: str) -> List[SSHSession]:
        return [s for s in self._sessions if s.group_id == group_id]

    def ungrouped_sessions(self) -> List[SSHSession]:
        return [s for s in self._sessions if not s.group_id]

    def add_session(self, session: SSHSession):
        self._sessions.append(session)
        self.save()

    def update_session(self, session: SSHSession):
        for i, s in enumerate(self._sessions):
            if s.id == session.id:
                self._sessions[i] = session
                self.save()
                return
        self.add_session(session)

    def delete_session(self, session_id: str):
        self._sessions = [s for s in self._sessions if s.id != session_id]
        self.save()

    # --- SSH config import ---

    def import_ssh_config(self, config_path=None) -> List[SSHSession]:
        """Parse ~/.ssh/config and return candidate sessions (skips wildcards)."""
        if config_path is None:
            config_path = os.path.expanduser("~/.ssh/config")
        if not os.path.exists(config_path):
            return []

        candidates = []
        existing_hosts = {(s.host, s.port, s.username) for s in self._sessions}

        try:
            with open(config_path, "r") as f:
                lines = f.readlines()
        except OSError:
            return []

        current_host = None
        current_data = {}

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Match key-value pairs
            match = re.match(r"(\w+)\s+(.+)", line)
            if not match:
                continue

            key = match.group(1).lower()
            value = match.group(2).strip()

            if key == "host":
                # Save previous host
                if current_host and current_data:
                    self._add_candidate(current_host, current_data,
                                        existing_hosts, candidates)
                # Start new host block
                current_host = value
                current_data = {}
            elif key == "hostname":
                current_data["hostname"] = value
            elif key == "port":
                try:
                    current_data["port"] = int(value)
                except ValueError:
                    pass
            elif key == "user":
                current_data["user"] = value
            elif key == "identityfile":
                current_data["identity_file"] = value

        # Handle last block
        if current_host and current_data:
            self._add_candidate(current_host, current_data,
                                existing_hosts, candidates)

        return candidates

    def _add_candidate(self, host_alias, data, existing_hosts, candidates):
        """Add a candidate session from ssh config parsing."""
        # Skip wildcard entries
        if "*" in host_alias or "?" in host_alias:
            return

        hostname = data.get("hostname", host_alias)
        port = data.get("port", 22)
        user = data.get("user", "")

        # Dedupe against existing
        if (hostname, port, user) in existing_hosts:
            return

        session = SSHSession(
            name=host_alias if host_alias != hostname else "",
            host=hostname,
            port=port,
            username=user,
            auth_method="key" if data.get("identity_file") else "password",
            identity_file=data.get("identity_file", ""),
        )
        candidates.append(session)

    # --- Remmina import ---

    def import_remmina(self, remmina_dir=None) -> List[SSHSession]:
        """Parse Remmina .remmina files and return SSH candidate sessions."""
        if remmina_dir is None:
            # Check common locations
            for candidate_dir in [
                os.path.expanduser("~/.local/share/remmina"),
                os.path.expanduser("~/.remmina"),
            ]:
                if os.path.isdir(candidate_dir):
                    remmina_dir = candidate_dir
                    break
        if not remmina_dir or not os.path.isdir(remmina_dir):
            return []

        existing_hosts = {(s.host, s.port, s.username) for s in self._sessions}
        candidates = []

        for filepath in sorted(glob.glob(os.path.join(remmina_dir, "*.remmina"))):
            try:
                cfg = configparser.ConfigParser()
                cfg.read(filepath)
                if not cfg.has_section("remmina"):
                    continue
                r = cfg["remmina"]

                # Only import SSH connections
                if r.get("protocol", "").upper() != "SSH":
                    continue

                name = r.get("name", "")
                server = r.get("server", "")
                username = r.get("username", "")
                group_name = r.get("group", "")
                identity_file = r.get("ssh_privatekey", "")
                exec_cmd = r.get("exec", "")

                if not server:
                    continue

                # Parse host:port
                host = server
                port = 22
                if ":" in server:
                    parts = server.rsplit(":", 1)
                    host = parts[0]
                    try:
                        port = int(parts[1])
                    except ValueError:
                        pass

                # Dedupe
                if (host, port, username) in existing_hosts:
                    continue

                auth_method = "key" if identity_file else "password"

                session = SSHSession(
                    name=name,
                    host=host,
                    port=port,
                    username=username,
                    auth_method=auth_method,
                    identity_file=identity_file,
                    startup_command=exec_cmd,
                )
                # Stash group name for caller to use
                session._remmina_group = group_name
                candidates.append(session)

            except (configparser.Error, OSError):
                continue

        return candidates
