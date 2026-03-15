"""SOS Tech branded splash screen for SOSterm."""

import os
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import (
    QPainter, QColor, QFont, QPixmap, QLinearGradient, QPen, QPainterPath,
)
from PyQt5.QtWidgets import QWidget

# Brand colors (matching SOSmail)
_BRAND_BLUE = QColor("#0047FF")
_TEXT_DARK = QColor("#2c2c2c")
_TEXT_MID = QColor("#6e7a8a")
_TEXT_LIGHT = QColor("#8a94a0")
_BORDER = QColor("#c0c8d4")
_LOADER_TRACK = QColor("#d0d5dd")
_GRAD_TOP = QColor("#f5f7fa")
_GRAD_BOTTOM = QColor("#e8ecf1")

# Layout constants
_WIDTH = 420
_HEIGHT = 360
_LOGO_MAX_W = 180
_CORNER_RADIUS = 10


class SplashScreen(QWidget):
    """Frameless branded splash shown during startup."""

    def __init__(self, version="", parent=None):
        super().__init__(parent)
        self._version = version
        self._status = "Loading..."

        # Animation progress values (0.0 → 1.0)
        self._fade_logo = 0.0
        self._fade_name = 0.0
        self._fade_tagline = 0.0
        self._fade_loader = 0.0
        self._fade_url = 0.0
        self._fade_version = 0.0
        self._loader_pos = 0.0  # 0.0 → 1.0 cycling

        # Window setup
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool  # skip taskbar
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(_WIDTH, _HEIGHT)

        # Center on screen
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(
                geo.x() + (geo.width() - _WIDTH) // 2,
                geo.y() + (geo.height() - _HEIGHT) // 2,
            )

        # Load logo
        self._logo = QPixmap()
        logo_path = os.path.join(os.path.dirname(__file__), "resources", "sos-logo.png")
        if not os.path.exists(logo_path):
            logo_path = "/opt/SOSterm/resources/sos-logo.png"
        if os.path.exists(logo_path):
            self._logo = QPixmap(logo_path)
            if not self._logo.isNull():
                self._logo = self._logo.scaledToWidth(
                    _LOGO_MAX_W, Qt.SmoothTransformation
                )

        # Fonts
        self._font_name = QFont("Segoe UI", 26, QFont.Bold)
        self._font_name.setLetterSpacing(QFont.AbsoluteSpacing, 1.0)
        self._font_tagline = QFont("Segoe UI", 10)
        self._font_status = QFont("Segoe UI", 9)
        self._font_url = QFont("Segoe UI", 11, QFont.DemiBold)
        self._font_version = QFont("Segoe UI", 8)

        # Staggered fade-in animations
        self._start_fade("fade_logo", 0)
        self._start_fade("fade_name", 200)
        self._start_fade("fade_tagline", 400)
        self._start_fade("fade_loader", 600)
        self._start_fade("fade_url", 800)
        self._start_fade("fade_version", 1000)

        # Loader bar animation (cycles continuously)
        self._loader_anim = QPropertyAnimation(self, b"loader_pos")
        self._loader_anim.setStartValue(0.0)
        self._loader_anim.setEndValue(1.0)
        self._loader_anim.setDuration(1400)
        self._loader_anim.setEasingCurve(QEasingCurve.InOutSine)
        self._loader_anim.setLoopCount(-1)
        self._loader_anim.start()

    # --- Qt properties for QPropertyAnimation ---

    def _get_fade_logo(self):
        return self._fade_logo

    def _set_fade_logo(self, v):
        self._fade_logo = v
        self.update()

    fade_logo = pyqtProperty(float, _get_fade_logo, _set_fade_logo)

    def _get_fade_name(self):
        return self._fade_name

    def _set_fade_name(self, v):
        self._fade_name = v
        self.update()

    fade_name = pyqtProperty(float, _get_fade_name, _set_fade_name)

    def _get_fade_tagline(self):
        return self._fade_tagline

    def _set_fade_tagline(self, v):
        self._fade_tagline = v
        self.update()

    fade_tagline = pyqtProperty(float, _get_fade_tagline, _set_fade_tagline)

    def _get_fade_loader(self):
        return self._fade_loader

    def _set_fade_loader(self, v):
        self._fade_loader = v
        self.update()

    fade_loader = pyqtProperty(float, _get_fade_loader, _set_fade_loader)

    def _get_fade_url(self):
        return self._fade_url

    def _set_fade_url(self, v):
        self._fade_url = v
        self.update()

    fade_url = pyqtProperty(float, _get_fade_url, _set_fade_url)

    def _get_fade_version(self):
        return self._fade_version

    def _set_fade_version(self, v):
        self._fade_version = v
        self.update()

    fade_version = pyqtProperty(float, _get_fade_version, _set_fade_version)

    def _get_loader_pos(self):
        return self._loader_pos

    def _set_loader_pos(self, v):
        self._loader_pos = v
        self.update()

    loader_pos = pyqtProperty(float, _get_loader_pos, _set_loader_pos)

    # --- Helpers ---

    def _start_fade(self, prop_name, delay_ms):
        """Create a fade-in animation for the given property after a delay."""
        anim = QPropertyAnimation(self, prop_name.encode())
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setDuration(600)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        # Store reference so it isn't garbage-collected
        setattr(self, f"_anim{prop_name}", anim)
        QTimer.singleShot(delay_ms, anim.start)

    def set_status(self, text):
        self._status = text
        self.update()

    # --- Paint ---

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # Rounded rect background with gradient
        path = QPainterPath()
        path.addRoundedRect(0.0, 0.0, _WIDTH, _HEIGHT, _CORNER_RADIUS, _CORNER_RADIUS)
        grad = QLinearGradient(0, 0, 0, _HEIGHT)
        grad.setColorAt(0, _GRAD_TOP)
        grad.setColorAt(1, _GRAD_BOTTOM)
        p.fillPath(path, grad)

        # Border
        p.setPen(QPen(_BORDER, 1))
        p.drawRoundedRect(0, 0, _WIDTH - 1, _HEIGHT - 1, _CORNER_RADIUS, _CORNER_RADIUS)

        cx = _WIDTH // 2  # horizontal center
        y = 50  # starting y

        # --- Logo ---
        if not self._logo.isNull() and self._fade_logo > 0:
            p.setOpacity(self._fade_logo)
            lx = cx - self._logo.width() // 2
            offset = int(8 * (1 - self._fade_logo))
            p.drawPixmap(lx, y + offset, self._logo)
            p.setOpacity(1.0)
        y += (self._logo.height() if not self._logo.isNull() else 54) + 24

        # --- App name: "f" dark + "term" blue ---
        if self._fade_name > 0:
            p.setOpacity(self._fade_name)
            p.setFont(self._font_name)
            fm = p.fontMetrics()
            sos_width = fm.horizontalAdvance("SOS")
            term_width = fm.horizontalAdvance("term")
            total = sos_width + term_width
            nx = cx - total // 2
            offset = int(8 * (1 - self._fade_name))
            p.setPen(_TEXT_DARK)
            p.drawText(nx, y + fm.ascent() + offset, "SOS")
            p.setPen(_BRAND_BLUE)
            p.drawText(nx + sos_width, y + fm.ascent() + offset, "term")
            p.setOpacity(1.0)
        y += 36

        # --- Tagline ---
        if self._fade_tagline > 0:
            p.setOpacity(self._fade_tagline)
            p.setFont(self._font_tagline)
            offset = int(8 * (1 - self._fade_tagline))
            p.setPen(_TEXT_MID)
            p.drawText(0, y + offset, _WIDTH, 20, Qt.AlignHCenter, "by S.O.S. Tech Services")
            p.setOpacity(1.0)
        y += 36

        # --- Loading bar ---
        if self._fade_loader > 0:
            p.setOpacity(self._fade_loader)
            bar_w = 120
            bar_h = 3
            bx = cx - bar_w // 2
            # Track
            p.setPen(Qt.NoPen)
            p.setBrush(_LOADER_TRACK)
            p.drawRoundedRect(bx, y, bar_w, bar_h, 2, 2)
            # Moving bar
            fill_w = int(bar_w * 0.4)
            # Map loader_pos 0→1 to bar traveling left-to-right and back
            pos = self._loader_pos
            travel = bar_w - fill_w
            if pos < 0.5:
                fx = bx + int(travel * (pos * 2))
            else:
                fx = bx + int(travel * ((1 - pos) * 2))
            p.setBrush(_BRAND_BLUE)
            # Clip to track bounds
            p.save()
            p.setClipRect(bx, y, bar_w, bar_h)
            p.drawRoundedRect(fx, y, fill_w, bar_h, 2, 2)
            p.restore()
            p.setOpacity(1.0)
        y += 16

        # --- Status text ---
        if self._fade_loader > 0:
            p.setOpacity(self._fade_loader)
            p.setFont(self._font_status)
            p.setPen(_TEXT_MID)
            p.drawText(0, y, _WIDTH, 18, Qt.AlignHCenter, self._status)
            p.setOpacity(1.0)
        y += 28

        # --- URL ---
        if self._fade_url > 0:
            p.setOpacity(self._fade_url)
            p.setFont(self._font_url)
            offset = int(8 * (1 - self._fade_url))
            p.setPen(_BRAND_BLUE)
            p.drawText(0, y + offset, _WIDTH, 20, Qt.AlignHCenter, "sos-tech.ca")
            p.setOpacity(1.0)

        # --- Version ---
        if self._fade_version > 0:
            p.setOpacity(self._fade_version)
            p.setFont(self._font_version)
            p.setPen(_TEXT_LIGHT)
            p.drawText(
                0, _HEIGHT - 30, _WIDTH - 20, 20,
                Qt.AlignRight | Qt.AlignBottom,
                f"v{self._version}",
            )
            p.setOpacity(1.0)

        p.end()
