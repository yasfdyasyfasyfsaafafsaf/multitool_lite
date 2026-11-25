import sys
import os
import json
import copy
import math
import ctypes
import tempfile
from ctypes import wintypes

from PyQt5.QtCore import Qt, QLineF, QPointF, QRectF, QTimer, QUrl
from PyQt5.QtGui import (
    QColor, QDesktopServices, QFont, QIcon, QImage, QLinearGradient,
    QPainter, QPen, QPixmap, QPolygonF, QRadialGradient,
)
from PyQt5.QtWidgets import (
    QAction, QApplication, QCheckBox, QColorDialog, QComboBox, QDialog,
    QDoubleSpinBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QMenu, QPlainTextEdit, QPushButton, QScrollArea, QSlider, QSpinBox,
    QSystemTrayIcon, QTabWidget, QVBoxLayout, QWidget,
)
from PyQt5.QtCore import QSharedMemory

APP_NAME = "MultitoolLite"
DISPLAY_NAME = "Multitool Lite"
CONFIG_DIR = os.path.join(
    os.environ.get("APPDATA", os.path.expanduser("~")), APP_NAME)
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

STYLES = {
    "lines": "Обычный",
    "dot": "Точка",
    "circle": "Кружок",
    "plus": "Плюсик",
    "t_shape": "T-образный",
    "x_shape": "X-образный",
    "square": "Квадрат",
    "chevron": "Шеврон",
    "diamond": "Ромб",
    "brackets": "Углы",
    "four_dot": "Четыре точки",
}

DEFAULT_CONFIG = {
    "theme": "dark",
    "enabled": True,
    "style": "lines",
    "color": "#00ff00",
    "rgb_enabled": False,
    "size": 8.0,
    "thickness": 2.0,
    "gap": 4,
    "opacity": 100,
    "outline": 1,
    "ox": 0,
    "oy": 0,
    "center_dot": False,
    "center_dot_size": 3,
    "glow_enabled": False,
    "g_color": "#ffffff",
    "g_radius": 85,
    "g_intensity": 40,
    "g_soft": 60,
    "g_ox": 0,
    "g_oy": 0,
    "dynamic_enabled": False,
    "dynamic_expand": 50,
    "dynamic_speed": 2,
}

INT_RANGES = {
    "gap": (0, 40), "opacity": (5, 100), "outline": (0, 5),
    "ox": (-100, 100), "oy": (-100, 100),
    "center_dot_size": (1, 30),
    "g_radius": (20, 400), "g_intensity": (0, 100), "g_soft": (0, 100),
    "g_ox": (-200, 200), "g_oy": (-200, 200),
    "dynamic_expand": (10, 100), "dynamic_speed": (1, 5),
}
BOOL_KEYS = ("enabled", "rgb_enabled", "center_dot", "glow_enabled",
             "dynamic_enabled")
COLOR_KEYS = ("color", "g_color")

THEME_COLORS = {
    "light": {
        "window": "#f3f6fb", "text": "#202b3c", "title": "#17243a",
        "muted": "#748198", "section": "#526785", "card": "#ffffff",
        "border": "#e2e8f0", "checkbox": "#39475c", "field": "#f8fafc",
        "border_hover": "#9db5d9", "accent": "#3d70c9",
        "button": "#f4f7fb", "button_text": "#34445c",
        "button_hover": "#eaf1fb", "button_pressed": "#dce8f8",
        "slider_track": "#e2e8f0", "slider_fill": "#7297d2",
        "slider_handle": "#5d82c1", "scroll_handle": "#cbd5e1",
        "tab": "#eaf0f7", "status_bg": "#e8f7ef",
        "status_border": "#c9ecd8", "status_text": "#24804a",
        "accent_text": "#ffffff",
    },
    "dark": {
        "window": "#101722", "text": "#dce5f2", "title": "#f0f5ff",
        "muted": "#91a0b7", "section": "#a8b8d0", "card": "#171f2b",
        "border": "#2a3545", "checkbox": "#c7d2e3", "field": "#111925",
        "border_hover": "#536985", "accent": "#7098d7",
        "button": "#202b3b", "button_text": "#d8e2f1",
        "button_hover": "#29384d", "button_pressed": "#334660",
        "slider_track": "#2c394b", "slider_fill": "#6c93d2",
        "slider_handle": "#80a5e0", "scroll_handle": "#3a4a60",
        "tab": "#1c2736", "status_bg": "#183126",
        "status_border": "#28543b", "status_text": "#8fdaa9",
        "accent_text": "#101722",
    },
}

UI_STYLESHEET = """
    QWidget#mainWindow {
        background: @window@;
        color: @text@;
        font-family: "Segoe UI";
        font-size: 10pt;
    }
    QWidget#mainWindow QWidget { color: @text@; }
    QDialog#supportDialog {
        background: @window@;
        color: @text@;
    }
    QLabel { color: @text@; }
    QLabel#appTitle {
        color: @title@;
        font-size: 19pt;
        font-weight: 700;
    }
    QLabel#sectionEyebrow {
        color: @section@;
        font-size: 8pt;
        font-weight: 700;
        letter-spacing: 1px;
    }
    QLabel#previewTitle { color: @title@; font-size: 11pt; font-weight: 700; }
    QLabel#configHint, QLabel#configStatus {
        color: @muted@;
    }
    QLabel#configStatus[success="true"] { color: @status_text@; }
    QWidget#previewCard {
        background: @card@;
        border: 1px solid @border@;
        border-radius: 16px;
    }
    QWidget#settingsPane { background: transparent; }
    QScrollArea { background: transparent; border: none; }
    QTabWidget::pane {
        background: @window@;
        border: 1px solid @border@;
        border-radius: 12px;
        top: -1px;
    }
    QTabBar::tab {
        background: @tab@;
        border: 1px solid @border@;
        border-bottom: none;
        border-top-left-radius: 9px;
        border-top-right-radius: 9px;
        color: @muted@;
        margin-right: 5px;
        padding: 10px 26px;
    }
    QTabBar::tab:selected {
        background: @card@;
        color: @accent@;
        font-weight: 700;
    }
    QTabBar::tab:hover { color: @text@; }
    QGroupBox {
        background: @card@;
        border: 1px solid @border@;
        border-radius: 12px;
        margin-top: 12px;
        padding: 16px 12px 10px 12px;
        font-weight: 600;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 5px;
        color: @section@;
    }
    QCheckBox { spacing: 7px; color: @checkbox@; }
    QCheckBox::indicator {
        background: @field@;
        border: 1px solid @border_hover@;
        border-radius: 4px;
        height: 15px;
        width: 15px;
    }
    QCheckBox::indicator:checked {
        background: @accent@;
        border-color: @accent@;
    }
    QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit, QPlainTextEdit {
        background: @field@;
        border: 1px solid @border@;
        border-radius: 7px;
        color: @text@;
        min-height: 28px;
        padding: 2px 8px;
        selection-background-color: @accent@;
    }
    QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover,
    QLineEdit:hover, QPlainTextEdit:hover { border-color: @border_hover@; }
    QComboBox QAbstractItemView {
        background: @field@;
        border: 1px solid @border@;
        color: @text@;
        selection-background-color: @accent@;
        selection-color: @accent_text@;
        outline: 0;
    }
    QPlainTextEdit { font-family: Consolas; }
    QPushButton {
        background: @button@;
        border: 1px solid @border@;
        border-radius: 8px;
        color: @button_text@;
        min-height: 28px;
        padding: 2px 10px;
    }
    QPushButton:hover {
        background: @button_hover@;
        border-color: @border_hover@;
    }
    QPushButton:pressed { background: @button_pressed@; }
    QPushButton#primaryAction {
        background: @accent@;
        border-color: @accent@;
        color: @accent_text@;
        font-weight: 700;
    }
    QPushButton#primaryAction:hover { background: @border_hover@; }
    QPushButton#supportAccordion {
        background: @button@;
        color: @button_text@;
        font-weight: 700;
        padding: 6px;
        text-align: left;
    }
    QLabel a { color: @accent@; }
    QSlider::groove:horizontal {
        background: @slider_track@;
        border-radius: 2px;
        height: 5px;
    }
    QSlider::sub-page:horizontal {
        background: @slider_fill@;
        border-radius: 2px;
    }
    QSlider::handle:horizontal {
        background: @card@;
        border: 2px solid @slider_handle@;
        border-radius: 7px;
        height: 12px;
        margin: -5px 0;
        width: 12px;
    }
    QScrollBar:vertical {
        background: transparent;
        margin: 2px;
        width: 9px;
    }
    QScrollBar::handle:vertical {
        background: @scroll_handle@;
        border-radius: 4px;
        min-height: 28px;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0;
    }
"""


class WheelSafeMixin:
    def wheelEvent(self, event):
        parent = self.parentWidget()
        while parent is not None and not isinstance(parent, QScrollArea):
            parent = parent.parentWidget()
        if parent is None:
            event.ignore()
            return

        scrollbar = parent.verticalScrollBar()
        delta = event.pixelDelta().y()
        if not delta:
            steps = event.angleDelta().y() / 120
            delta = round(steps * max(24, scrollbar.singleStep() * 3))
        if delta:
            scrollbar.setValue(scrollbar.value() - delta)
        event.accept()


class WheelSafeComboBox(WheelSafeMixin, QComboBox):
    pass


class WheelSafeSpinBox(WheelSafeMixin, QSpinBox):
    pass


class WheelSafeDoubleSpinBox(WheelSafeMixin, QDoubleSpinBox):
    pass


class WheelSafeSlider(WheelSafeMixin, QSlider):
    pass


# ------------------------------------------------------------------ config
def normalize_config(raw):
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    if isinstance(raw, dict):
        for key in DEFAULT_CONFIG:
            if key in raw:
                cfg[key] = raw[key]
    if cfg["theme"] not in THEME_COLORS:
        cfg["theme"] = DEFAULT_CONFIG["theme"]
    if cfg["style"] not in STYLES:
        cfg["style"] = DEFAULT_CONFIG["style"]
    for key in COLOR_KEYS:
        color = QColor(cfg[key]) if isinstance(cfg[key], str) else QColor()
        cfg[key] = color.name() if color.isValid() else DEFAULT_CONFIG[key]
    for key, (low, high) in INT_RANGES.items():
        value = cfg[key]
        if type(value) is not int:
            value = DEFAULT_CONFIG[key]
        cfg[key] = max(low, min(high, value))
    for key in ("size", "thickness"):
        value = cfg[key]
        if (type(value) not in (int, float) or isinstance(value, bool)
                or not math.isfinite(value)):
            value = DEFAULT_CONFIG[key]
        cfg[key] = round(max(0.01, min(100.0, float(value))), 2)
    for key in BOOL_KEYS:
        if type(cfg[key]) is not bool:
            cfg[key] = DEFAULT_CONFIG[key]
    return cfg


def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as handle:
            return normalize_config(json.load(handle))
    except (OSError, ValueError):
        return copy.deepcopy(DEFAULT_CONFIG)


def save_config(cfg):
    temporary = None
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(
            prefix=".config-", suffix=".tmp", dir=CONFIG_DIR)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(cfg, handle, ensure_ascii=False, indent=2)
        os.replace(temporary, CONFIG_PATH)
    except OSError:
        if temporary and os.path.exists(temporary):
            try:
                os.remove(temporary)
            except OSError:
                pass


# ------------------------------------------------------------------ мышь
def is_left_mouse_button_down():
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.GetAsyncKeyState.argtypes = (ctypes.c_int,)
    user32.GetAsyncKeyState.restype = ctypes.c_short
    return bool(user32.GetAsyncKeyState(0x01) & 0x8000)


# ------------------------------------------------------------------ прицел
def aligned_center(value, thickness):
    k = math.floor(value)
    return k + 0.5 if int(round(thickness)) % 2 else float(k)


def draw_shape(p, style, c, size, gap, t, color, extra, center_y=None,
               point_color=None):
    t = max(t, 1.0)
    size = max(size, 1.0)
    gap = max(gap, 0.0)
    cy_raw = c if center_y is None else center_y
    if style == "dot":
        cx = aligned_center(c, size)
        cy = aligned_center(cy_raw, size)
    else:
        cx = aligned_center(c, t)
        cy = aligned_center(cy_raw, t)
    pen = QPen(color, t + 2 * extra)
    pen.setCapStyle(Qt.FlatCap)
    pen.setJoinStyle(Qt.MiterJoin)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    e = extra

    def arm_span(center, a, b):
        frac = center - math.floor(center)
        if a < 0 < b:
            half = b + (0.5 if frac else 0.0)
            return center - half, center + half
        if a >= 0:
            lo = math.ceil(round(center + a, 6))
            return lo, lo + (b - a)
        hi = math.floor(round(center + b, 6))
        return hi - (b - a), hi

    def h(a, b):
        lo, hi = arm_span(cx, a, b)
        p.drawLine(QLineF(lo - e, cy, hi + e, cy))

    def v(a, b):
        lo, hi = arm_span(cy, a, b)
        p.drawLine(QLineF(cx, lo - e, cx, hi + e))

    def fill_dot(x, y, diam, dot_color):
        diam = max(diam, 1.0)
        p.setPen(Qt.NoPen)
        p.setBrush(dot_color)
        if diam <= 3.0:
            side = max(1, int(round(diam))) + 2 * e
            left = math.floor(x - side / 2 + 0.5)
            top = math.floor(y - side / 2 + 0.5)
            p.drawRect(QRectF(left, top, side, side))
        else:
            r = diam / 2 + e
            p.drawEllipse(QPointF(x, y), r, r)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)

    if style in ("lines", "t_shape"):
        if gap == 0:
            h(-size, size)
            if style == "t_shape":
                v(0, size)
            else:
                v(-size, size)
        else:
            h(-(gap + size), -gap)
            h(gap, gap + size)
            v(gap, gap + size)
            if style != "t_shape":
                v(-(gap + size), -gap)
    elif style == "plus":
        h(-size, size)
        v(-size, size)
    elif style == "dot":
        fill_dot(cx, cy, max(size, 0.01), point_color or color)
    elif style == "circle":
        p.drawEllipse(QPointF(cx, cy), size, size)
    elif style == "x_shape":
        g = gap * 0.7071
        s = size * 0.7071
        for sx in (-1, 1):
            for sy in (-1, 1):
                p.drawLine(QLineF(cx + sx * g, cy + sy * g,
                                  cx + sx * (g + s), cy + sy * (g + s)))
    elif style == "square":
        p.drawRect(QRectF(cx - size, cy - size, 2 * size, 2 * size))
    elif style == "chevron":
        s = size * 0.8
        p.drawPolyline(QPointF(cx - s, cy + gap + s), QPointF(cx, cy + gap),
                       QPointF(cx + s, cy + gap + s))
    elif style == "diamond":
        s = size + gap
        p.drawPolygon(QPolygonF([
            QPointF(cx, cy - s), QPointF(cx + s, cy),
            QPointF(cx, cy + s), QPointF(cx - s, cy)]))
    elif style == "brackets":
        start, end = gap, gap + size
        for sx in (-1, 1):
            for sy in (-1, 1):
                p.drawLine(QPointF(cx + sx * start, cy + sy * start),
                           QPointF(cx + sx * end, cy + sy * start))
                p.drawLine(QPointF(cx + sx * start, cy + sy * start),
                           QPointF(cx + sx * start, cy + sy * end))
    elif style == "four_dot":
        radius = gap + size / 2
        for dx, dy in ((0, -radius), (radius, 0), (0, radius), (-radius, 0)):
            fill_dot(cx + dx, cy + dy, t, point_color or color)


def center_dot_diameter(cfg):
    diameter = max(1, int(round(cfg.get("center_dot_size", 3))))
    if diameter % 2 != max(1, int(round(cfg["thickness"]))) % 2:
        diameter += 1
    return diameter


def draw_crosshair(p, cfg, cx, cy, color=None, gap_offset=0):
    draw_cfg = cfg
    if gap_offset:
        draw_cfg = dict(cfg)
        draw_cfg["gap"] = cfg["gap"] + gap_offset
    main_color = QColor(color or cfg["color"])
    outline_color = QColor(0, 0, 0)
    outline = cfg["outline"]
    dot = center_dot_diameter(cfg) if cfg.get("center_dot") else 0
    if outline > 0:
        draw_shape(p, draw_cfg["style"], cx, draw_cfg["size"], draw_cfg["gap"],
                   draw_cfg["thickness"], outline_color, outline, cy,
                   outline_color)
        if dot:
            draw_shape(p, "dot", cx, dot, 0, 1, outline_color, outline, cy,
                       outline_color)
    draw_shape(p, draw_cfg["style"], cx, draw_cfg["size"], draw_cfg["gap"],
               draw_cfg["thickness"], main_color, 0, cy, main_color)
    if dot:
        draw_shape(p, "dot", cx, dot, 0, 1, main_color, 0, cy, main_color)


def render_crosshair_size(cfg, max_gap_offset=0):
    size, t, gap, ow = cfg["size"], cfg["thickness"], cfg["gap"], cfg["outline"]
    if cfg.get("center_dot"):
        size = max(size, cfg.get("center_dot_size", 3))
    ext = int(max(size, 1.0) + gap + max_gap_offset + max(t, 1.0) + ow + 6)
    return ext * 2 + 1, ext + 0.5


def smoothstep(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def render_glow(cfg):
    r = max(int(cfg["g_radius"]), 5)
    dim = r * 2 + 4
    img = QImage(dim, dim, QImage.Format_ARGB32_Premultiplied)
    img.fill(Qt.transparent)
    base = QColor(cfg["g_color"])
    peak = 255 * cfg["g_intensity"] / 100.0
    core = 0.85 * (1 - cfg["g_soft"] / 100.0)
    c = dim / 2
    grad = QRadialGradient(c, c, r)
    steps = 20
    for i in range(steps + 1):
        t = i / steps
        f = 1.0 if t <= core else 1.0 - smoothstep(
            (t - core) / max(1e-6, 1 - core))
        col = QColor(base)
        col.setAlpha(int(peak * f))
        grad.setColorAt(t, col)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.setPen(Qt.NoPen)
    p.setBrush(grad)
    p.drawEllipse(QPointF(c, c), r, r)
    p.end()
    return img


# ------------------------------------------------------------------ оверлей
OVERLAY_FLAGS = (
    Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
    | Qt.WindowTransparentForInput | Qt.WindowDoesNotAcceptFocus)


class Overlay(QWidget):
    """Окно-оверлей по центру экрана. kind: 'cross' или 'glow'."""

    def __init__(self, get_cfg, kind, get_color=None):
        super().__init__()
        self.get_cfg = get_cfg
        self.kind = kind
        self.get_color = get_color
        self.dynamic_gap = 0
        self.glow_img = None
        self._glow_key = None
        self.setWindowFlags(OVERLAY_FLAGS)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.refresh()

    def refresh(self):
        cfg = self.get_cfg()
        if self.kind == "cross":
            max_gap = 0
            if cfg["dynamic_enabled"]:
                max_gap = math.ceil(
                    cfg["size"] * cfg["dynamic_expand"] / 100.0)
            dim, _center = render_crosshair_size(cfg, max_gap)
            ox, oy = cfg["ox"], cfg["oy"]
        else:
            glow_key = (
                cfg["g_color"], cfg["g_radius"],
                cfg["g_intensity"], cfg["g_soft"])
            if cfg["glow_enabled"] and glow_key != self._glow_key:
                self.glow_img = render_glow(cfg)
                self._glow_key = glow_key
            dim = cfg["g_radius"] * 2 + 4
            ox, oy = cfg["g_ox"], cfg["g_oy"]
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.geometry()
        cx = geo.x() + geo.width() // 2
        cy = geo.y() + geo.height() // 2
        self.setGeometry(cx - dim // 2 + ox, cy - dim // 2 + oy, dim, dim)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        if self.kind == "cross":
            cfg = self.get_cfg()
            p.setOpacity(cfg["opacity"] / 100.0)
            p.setRenderHint(QPainter.Antialiasing, True)
            draw_crosshair(
                p, cfg, self.width() / 2, self.height() / 2,
                self.get_color() if self.get_color else None,
                self.dynamic_gap)
        elif self.glow_img is not None:
            p.drawImage(0, 0, self.glow_img)


class CrosshairPreview(QWidget):
    def __init__(
            self, get_cfg, get_color, get_dynamic_level, get_glow_image,
            parent=None):
        super().__init__(parent)
        self.get_cfg = get_cfg
        self.get_color = get_color
        self.get_dynamic_level = get_dynamic_level
        self.get_glow_image = get_glow_image
        self.setObjectName("crosshairPreview")
        self.setMinimumSize(230, 230)

    def paintEvent(self, _event):
        cfg = self.get_cfg()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        canvas = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        painter.setPen(QPen(QColor("#dce4ef"), 1))
        painter.setBrush(QColor("#172131"))
        painter.drawRoundedRect(canvas, 16, 16)

        painter.save()
        painter.setClipRect(canvas.adjusted(1, 1, -1, -1))
        grid_pen = QPen(QColor(255, 255, 255, 13), 1)
        painter.setPen(grid_pen)
        spacing = 24
        x = int(canvas.left()) + spacing
        while x < canvas.right():
            painter.drawLine(x, int(canvas.top()), x, int(canvas.bottom()))
            x += spacing
        y = int(canvas.top()) + spacing
        while y < canvas.bottom():
            painter.drawLine(int(canvas.left()), y, int(canvas.right()), y)
            y += spacing

        cx, cy = canvas.center().x(), canvas.center().y()
        glow_img = self.get_glow_image()
        if cfg["glow_enabled"] and glow_img is not None:
            glow_size = glow_img.width() * 0.28
            glow_rect = QRectF(
                cx - glow_size / 2, cy - glow_size / 2,
                glow_size, glow_size)
            painter.drawImage(glow_rect, glow_img)

        painter.setPen(QPen(QColor(255, 255, 255, 28), 1))
        painter.drawLine(QPointF(cx - 36, cy), QPointF(cx + 36, cy))
        painter.drawLine(QPointF(cx, cy - 36), QPointF(cx, cy + 36))

        dynamic_gap = round(
            cfg["size"] * self.get_dynamic_level()
            * cfg["dynamic_expand"] / 100.0)
        painter.save()
        painter.translate(cx, cy)
        painter.scale(0.72, 0.72)
        painter.setOpacity(cfg["opacity"] / 100.0)
        draw_crosshair(
            painter, cfg, 0, 0, self.get_color(), dynamic_gap)
        painter.restore()
        painter.restore()


# ------------------------------------------------------------------ иконка
def make_app_icon():
    icon = QIcon()
    for s in (16, 24, 32, 48, 64, 128):
        pm = QPixmap(s, s)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing, True)
        grad = QLinearGradient(0, 0, 0, s)
        grad.setColorAt(0.0, QColor("#2a2444"))
        grad.setColorAt(1.0, QColor("#09090b"))
        p.setBrush(grad)
        p.setPen(QPen(QColor("#3f3f46"), max(1.0, s / 48)))
        radius = s * 0.28
        p.drawRoundedRect(QRectF(0.5, 0.5, s - 1, s - 1), radius, radius)
        pen = QPen(QColor("#8b7cff"), max(1.0, s / 14))
        pen.setCapStyle(Qt.FlatCap)
        p.setPen(pen)
        c = s / 2
        gap, arm = s * 0.11, s * 0.25
        p.drawLine(QPointF(c - gap - arm, c), QPointF(c - gap, c))
        p.drawLine(QPointF(c + gap, c), QPointF(c + gap + arm, c))
        p.drawLine(QPointF(c, c - gap - arm), QPointF(c, c - gap))
        p.drawLine(QPointF(c, c + gap), QPointF(c, c + gap + arm))
        p.end()
        icon.addPixmap(pm)
    return icon


# ------------------------------------------------------------------ окно
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.cfg = load_config()
        self.loading = True
        self.ctrls = {}
        self.rgb_hue = 0
        self.dynamic_level = 0.0
        QApplication.setFont(QFont("Segoe UI", 9))
        self.setWindowTitle(DISPLAY_NAME)
        self.setWindowIcon(make_app_icon())
        self.setObjectName("mainWindow")
        self.setMinimumSize(760, 560)
        self.resize(850, 660)
        self.apply_theme()

        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.setInterval(300)
        self.save_timer.timeout.connect(self.save_and_refresh_config)

        self.glow = Overlay(lambda: self.cfg, "glow")
        self.overlay = Overlay(lambda: self.cfg, "cross", self.cross_color)

        self.rgb_timer = QTimer(self)
        self.rgb_timer.setInterval(30)
        self.rgb_timer.timeout.connect(self.advance_rgb)
        self.dynamic_timer = QTimer(self)
        self.dynamic_timer.setInterval(16)
        self.dynamic_timer.timeout.connect(self.advance_dynamic)

        self.build_ui()
        self.build_tray()
        self.load_into_ui()
        self.loading = False
        self.apply_all()

    # --- состояние
    def apply_theme(self):
        palette = THEME_COLORS[self.cfg.get("theme", "dark")]
        stylesheet = UI_STYLESHEET
        for key, value in palette.items():
            stylesheet = stylesheet.replace(f"@{key}@", value)
        self.setStyleSheet(stylesheet)
        if hasattr(self, "color_btn"):
            self.update_color_buttons()

    def on_theme_changed(self, _index):
        if self.loading:
            return
        theme = self.theme_box.currentData()
        if theme not in THEME_COLORS:
            return
        self.cfg["theme"] = theme
        self.apply_theme()
        self.save_timer.start()

    def save_and_refresh_config(self):
        save_config(self.cfg)
        self.refresh_config_preview()

    def refresh_config_preview(self):
        if not hasattr(self, "config_preview"):
            return
        text = json.dumps(self.cfg, ensure_ascii=False, indent=2)
        if self.config_preview.toPlainText() != text:
            self.config_preview.setPlainText(text)

    def copy_config(self):
        self.refresh_config_preview()
        QApplication.clipboard().setText(self.config_preview.toPlainText())
        self.set_config_status("Конфиг скопирован в буфер обмена.", True)

    def copy_config_path(self):
        QApplication.clipboard().setText(os.path.abspath(CONFIG_PATH))
        self.set_config_status("Путь к конфигу скопирован.", True)

    def open_config_folder(self):
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
        except OSError as error:
            self.set_config_status(
                f"Не удалось открыть папку конфига: {error}", False)
            return
        opened = QDesktopServices.openUrl(
            QUrl.fromLocalFile(os.path.abspath(CONFIG_DIR)))
        if opened:
            self.set_config_status("Папка конфига открыта.", True)
        else:
            self.set_config_status("Не удалось открыть папку конфига.", False)

    def set_config_status(self, text, success):
        self.config_status.setText(text)
        self.config_status.setProperty("success", success)
        self.config_status.style().unpolish(self.config_status)
        self.config_status.style().polish(self.config_status)

    def cross_color(self):
        if self.cfg["rgb_enabled"]:
            return QColor.fromHsv(self.rgb_hue, 255, 255).name()
        return None

    def apply_all(self):
        self.glow.refresh()
        self.overlay.refresh()
        self.glow.setVisible(self.cfg["glow_enabled"])
        self.overlay.setVisible(self.cfg["enabled"])
        if hasattr(self, "preview"):
            self.preview.update()
        if self.cfg["rgb_enabled"]:
            self.rgb_timer.start()
        else:
            self.rgb_timer.stop()
            self.overlay.update()
        if self.cfg["dynamic_enabled"]:
            if not self.dynamic_timer.isActive():
                self.dynamic_timer.start()
        else:
            self.dynamic_timer.stop()
            self.dynamic_level = 0.0
            self.overlay.dynamic_gap = 0
            self.overlay.update()

    def set_val(self, key, value):
        if self.loading:
            return
        self.cfg[key] = value
        self.apply_all()
        self.save_timer.start()

    def advance_rgb(self):
        self.rgb_hue = (self.rgb_hue + 2) % 360
        self.overlay.update()
        self.preview.update()

    def advance_dynamic(self):
        try:
            pressed = is_left_mouse_button_down()
        except OSError:
            self.dynamic_timer.stop()
            return
        target = 1.0 if pressed else 0.0
        rate = 6.0 + self.cfg["dynamic_speed"] * 4.0
        self.dynamic_level += (target - self.dynamic_level) * (
            1.0 - math.exp(-rate * 0.016))
        gap = round(self.cfg["size"] * self.dynamic_level
                    * self.cfg["dynamic_expand"] / 100.0)
        if gap != self.overlay.dynamic_gap:
            self.overlay.dynamic_gap = gap
            self.overlay.update()
            self.preview.update()

    # --- интерфейс
    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(0)
        self.tabs = QTabWidget()
        root.addWidget(self.tabs)

        crosshair_tab = QWidget()
        tab_layout = QVBoxLayout(crosshair_tab)
        tab_layout.setContentsMargins(10, 14, 10, 8)
        tab_layout.setSpacing(16)

        header = QHBoxLayout()
        header.setSpacing(12)
        title_col = QVBoxLayout()
        title_col.setSpacing(1)
        title = QLabel(DISPLAY_NAME)
        title.setObjectName("appTitle")
        title_col.addWidget(title)
        header.addLayout(title_col)
        header.addStretch(1)
        tab_layout.addLayout(header)

        body = QHBoxLayout()
        body.setSpacing(14)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(400)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        inner = QWidget()
        inner.setObjectName("settingsPane")
        col = QVBoxLayout(inner)
        col.setContentsMargins(2, 2, 8, 2)
        col.setSpacing(0)
        scroll.setWidget(inner)
        body.addWidget(scroll, 1)

        preview_card = QWidget()
        preview_card.setObjectName("previewCard")
        preview_card.setFixedWidth(270)
        preview_layout = QVBoxLayout(preview_card)
        preview_layout.setContentsMargins(14, 14, 14, 14)
        preview_layout.setSpacing(12)
        preview_title = QLabel("Предпросмотр")
        preview_title.setObjectName("previewTitle")
        preview_layout.addWidget(preview_title)
        self.preview = CrosshairPreview(
            lambda: self.cfg, self.cross_color,
            lambda: self.dynamic_level, lambda: self.glow.glow_img,
            preview_card)
        preview_layout.addWidget(self.preview)
        preview_layout.addStretch(1)
        body.addWidget(preview_card, 0, Qt.AlignTop)
        tab_layout.addLayout(body, 1)

        # Прицел
        box = QGroupBox("Прицел")
        form = QFormLayout(box)
        form.setContentsMargins(12, 17, 12, 10)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)
        self.enabled_chk = QCheckBox("Показывать прицел")
        self.enabled_chk.toggled.connect(
            lambda v: self.set_val("enabled", v))
        form.addRow(self.enabled_chk)

        self.style_box = WheelSafeComboBox()
        for key, name in STYLES.items():
            self.style_box.addItem(name, key)
        self.style_box.currentIndexChanged.connect(
            lambda _i: self.set_val("style", self.style_box.currentData()))
        form.addRow("Форма:", self.style_box)

        color_row = QHBoxLayout()
        self.color_btn = QPushButton()
        self.color_btn.clicked.connect(lambda: self.pick_color("color"))
        self.rgb_chk = QCheckBox("RGB")
        self.rgb_chk.toggled.connect(
            lambda v: self.set_val("rgb_enabled", v))
        color_row.addWidget(self.color_btn, 1)
        color_row.addWidget(self.rgb_chk)
        form.addRow("Цвет:", color_row)

        self.add_slider(form, "Размер:", "size", 0.01, 100.0, True)
        self.add_slider(form, "Толщина:", "thickness", 0.01, 100.0, True)
        self.add_slider(form, "Зазор:", "gap", 0, 40)
        self.add_slider(form, "Прозрачность, %:", "opacity", 5, 100)
        self.add_slider(form, "Смещение X:", "ox", -100, 100)
        self.add_slider(form, "Смещение Y:", "oy", -100, 100)
        col.addWidget(box)

        # Обводка
        box = QGroupBox("Обводка")
        form = QFormLayout(box)
        form.setContentsMargins(12, 17, 12, 10)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)
        self.add_slider(form, "Толщина, px:", "outline", 0, 5)
        col.addWidget(box)

        # Точка в центре
        box = QGroupBox("Точка в центре")
        form = QFormLayout(box)
        form.setContentsMargins(12, 17, 12, 10)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)
        self.dot_chk = QCheckBox("Показывать точку")
        self.dot_chk.toggled.connect(lambda v: self.set_val("center_dot", v))
        form.addRow(self.dot_chk)
        self.add_slider(form, "Размер точки:", "center_dot_size", 1, 30)
        col.addWidget(box)

        # Подсветка
        box = QGroupBox("Подсветка")
        form = QFormLayout(box)
        form.setContentsMargins(12, 17, 12, 10)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)
        self.glow_chk = QCheckBox("Показывать подсветку")
        self.glow_chk.toggled.connect(
            lambda v: self.set_val("glow_enabled", v))
        form.addRow(self.glow_chk)
        self.gcolor_btn = QPushButton()
        self.gcolor_btn.clicked.connect(lambda: self.pick_color("g_color"))
        form.addRow("Цвет света:", self.gcolor_btn)
        self.add_slider(form, "Радиус:", "g_radius", 20, 400)
        self.add_slider(form, "Яркость, %:", "g_intensity", 0, 100)
        self.add_slider(form, "Мягкость края, %:", "g_soft", 0, 100)
        self.add_slider(form, "Смещение X:", "g_ox", -200, 200)
        self.add_slider(form, "Смещение Y:", "g_oy", -200, 200)
        col.addWidget(box)

        # Анимация
        box = QGroupBox("Анимация")
        form = QFormLayout(box)
        form.setContentsMargins(12, 17, 12, 10)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)
        self.dyn_chk = QCheckBox(
            "Расширять зазор при зажатой\nлевой кнопке мыши")
        self.dyn_chk.toggled.connect(
            lambda v: self.set_val("dynamic_enabled", v))
        form.addRow(self.dyn_chk)
        self.add_slider(form, "Увеличение зазора, %:", "dynamic_expand",
                        10, 100)
        self.add_slider(form, "Скорость реакции:", "dynamic_speed", 1, 5)
        col.addWidget(box)
        col.addStretch(1)

        support_btn = QPushButton("Тех. поддержка")
        support_btn.clicked.connect(self.open_support_dialog)
        tab_layout.addWidget(support_btn, 0, Qt.AlignRight)
        self.tabs.addTab(crosshair_tab, "Прицел")
        self.build_settings_tab()

    def build_settings_tab(self):
        settings_tab = QWidget()
        layout = QVBoxLayout(settings_tab)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        theme_group = QGroupBox("Оформление")
        theme_form = QFormLayout(theme_group)
        theme_form.setContentsMargins(14, 20, 14, 14)
        theme_form.setHorizontalSpacing(14)
        theme_form.setVerticalSpacing(8)
        self.theme_box = WheelSafeComboBox()
        self.theme_box.addItem("Светлая", "light")
        self.theme_box.addItem("Тёмная", "dark")
        self.theme_box.currentIndexChanged.connect(self.on_theme_changed)
        theme_form.addRow("Тема приложения:", self.theme_box)
        layout.addWidget(theme_group)

        config_group = QGroupBox("Конфигурация")
        config_layout = QVBoxLayout(config_group)
        config_layout.setContentsMargins(14, 20, 14, 14)
        config_layout.setSpacing(8)
        config_hint = QLabel(
            "Текущий конфиг можно скопировать как JSON или открыть папку "
            "с файлом.")
        config_hint.setObjectName("configHint")
        config_hint.setWordWrap(True)
        config_layout.addWidget(config_hint)

        config_layout.addWidget(QLabel("Путь к файлу:"))
        self.config_path = QLineEdit(os.path.abspath(CONFIG_PATH))
        self.config_path.setReadOnly(True)
        config_layout.addWidget(self.config_path)

        self.config_preview = QPlainTextEdit()
        self.config_preview.setReadOnly(True)
        self.config_preview.setMinimumHeight(190)
        self.config_preview.setPlaceholderText("Конфигурация появится здесь")
        config_layout.addWidget(self.config_preview, 1)

        actions = QHBoxLayout()
        self.copy_config_btn = QPushButton("Скопировать конфиг")
        self.copy_config_btn.setObjectName("primaryAction")
        self.copy_config_btn.clicked.connect(self.copy_config)
        actions.addWidget(self.copy_config_btn)
        self.copy_config_path_btn = QPushButton("Копировать путь")
        self.copy_config_path_btn.clicked.connect(self.copy_config_path)
        actions.addWidget(self.copy_config_path_btn)
        self.open_config_folder_btn = QPushButton("Открыть папку")
        self.open_config_folder_btn.clicked.connect(self.open_config_folder)
        actions.addWidget(self.open_config_folder_btn)
        config_layout.addLayout(actions)

        self.config_status = QLabel()
        self.config_status.setObjectName("configStatus")
        config_layout.addWidget(self.config_status)
        layout.addWidget(config_group, 1)
        self.tabs.addTab(settings_tab, "Настройки")

    def add_slider(self, form, label, key, low, high, decimal=False):
        slider = WheelSafeSlider(Qt.Horizontal)
        if decimal:
            spin = WheelSafeDoubleSpinBox()
            spin.setDecimals(2)
            spin.setSingleStep(0.01)
            spin.setRange(low, high)
            spin.setKeyboardTracking(False)
            slider.setRange(round(low * 100), round(high * 100))
            slider.setPageStep(100)
            slider.valueChanged.connect(
                lambda v, s=spin: s.setValue(v / 100))
            spin.valueChanged.connect(
                lambda v, s=slider: s.setValue(round(v * 100)))
        else:
            spin = WheelSafeSpinBox()
            spin.setRange(low, high)
            slider.setRange(low, high)
            slider.valueChanged.connect(spin.setValue)
            spin.valueChanged.connect(slider.setValue)
        spin.valueChanged.connect(lambda v, k=key: self.set_val(k, v))
        row = QHBoxLayout()
        row.addWidget(slider, 1)
        spin.setFixedWidth(76)
        row.addWidget(spin)
        form.addRow(label, row)
        self.ctrls[key] = (slider, spin)

    def load_into_ui(self):
        cfg = self.cfg
        self.theme_box.setCurrentIndex(
            self.theme_box.findData(cfg["theme"]))
        self.enabled_chk.setChecked(cfg["enabled"])
        self.style_box.setCurrentIndex(self.style_box.findData(cfg["style"]))
        self.rgb_chk.setChecked(cfg["rgb_enabled"])
        self.dot_chk.setChecked(cfg["center_dot"])
        self.glow_chk.setChecked(cfg["glow_enabled"])
        self.dyn_chk.setChecked(cfg["dynamic_enabled"])
        for key, (slider, spin) in self.ctrls.items():
            if key in ("size", "thickness"):
                slider.setValue(round(cfg[key] * 100))
            else:
                slider.setValue(cfg[key])
            spin.setValue(cfg[key])
        self.update_color_buttons()
        self.refresh_config_preview()

    def update_color_buttons(self):
        border = THEME_COLORS[self.cfg["theme"]]["border"]
        for button, key in ((self.color_btn, "color"),
                            (self.gcolor_btn, "g_color")):
            color = self.cfg[key]
            text = "black" if QColor(color).lightness() > 110 else "white"
            button.setText(color)
            button.setStyleSheet(
                f"background-color: {color}; color: {text}; "
                f"border: 1px solid {border}; padding: 4px;")

    def pick_color(self, key):
        color = QColorDialog.getColor(
            QColor(self.cfg[key]), self, "Выбор цвета")
        if color.isValid():
            self.cfg[key] = color.name()
            self.update_color_buttons()
            self.apply_all()
            self.save_timer.start()

    # --- тех. поддержка
    def open_support_dialog(self):
        dialog = QDialog(self)
        dialog.setObjectName("supportDialog")
        dialog.setStyleSheet(self.styleSheet())
        dialog.setWindowTitle("Тех. поддержка")
        dialog.setMinimumWidth(360)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(18, 18, 18, 14)
        layout.setSpacing(10)

        contacts = QLabel(
            'Скинуть баги, идеи, или что - то спросить: '
            'Телеграмм - <a href="https://t.me/amateww">@amateww</a><br><br>'
            'channel - <a href="https://t.me/bl00dsk">t.me/bl00dsk</a><br><br>'
            'Приложение создавалось для '
            '<a href="https://t.me/standknife">t.me/standknife</a>, '
            'на других приложениях я незнаю как работает.')
        contacts.setWordWrap(True)
        contacts.setOpenExternalLinks(True)
        layout.addWidget(contacts)

        def accordion(title, html):
            box = QWidget()
            lay = QVBoxLayout(box)
            lay.setContentsMargins(0, 5, 0, 5)
            header = QPushButton("▼ " + title)
            header.setObjectName("supportAccordion")
            content = QLabel(html)
            content.setOpenExternalLinks(True)
            content.setVisible(False)

            def toggle():
                visible = not content.isVisible()
                content.setVisible(visible)
                header.setText(("▲ " if visible else "▼ ") + title)

            header.clicked.connect(toggle)
            lay.addWidget(header)
            lay.addWidget(content)
            return box

        layout.addWidget(accordion(
            "Разработчики",
            "amateww — <a href='https://t.me/bl00dsk'>t.me/bl00dsk</a><br>"
            "claude pro — <a href='https://claude.ai'>claude.ai</a>"))
        layout.addWidget(accordion(
            "Тестеры",
            "Claude code Pro<br>"
            "claude desktop<br>"
            "claude free<br>"
            "Deepseek<br>"
            "ChatGPT<br>"
            "Gemini<br>"
            "Manera - no channel<br>"
            "scrltt — <a href='https://t.me/scrlttSK'>t.me/scrlttSK</a><br>"
            "Mitsuko — <a href='https://t.me/TradeMitsuko'>"
            "t.me/TradeMitsuko</a><br>"
            "whotoor — <a href='https://t.me/whotooryansky'>"
            "t.me/whotooryansky</a><br>"
            "dollar — <a href='https://t.me/paladinbad'>"
            "t.me/paladinbad</a>"))

        layout.addWidget(QLabel("Версия: v1.0 Lite"))
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn, 0, Qt.AlignRight)
        dialog.exec_()

    # --- трей
    def build_tray(self):
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(make_app_icon())
        self.tray.setToolTip(DISPLAY_NAME)
        menu = QMenu()
        open_action = QAction("Настройки", self)
        open_action.triggered.connect(self.show_window)
        quit_action = QAction("Выход", self)
        quit_action.triggered.connect(self.quit_app)
        menu.addAction(open_action)
        menu.addSeparator()
        menu.addAction(quit_action)
        self.tray_menu = menu
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()

    def show_window(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.DoubleClick, QSystemTrayIcon.Trigger):
            self.show_window()

    def closeEvent(self, event):
        # закрытие окна сворачивает в трей, прицел продолжает работать
        event.ignore()
        self.hide()

    def quit_app(self):
        self.save_timer.stop()
        save_config(self.cfg)
        self.tray.hide()
        self.glow.close()
        self.overlay.close()
        QApplication.quit()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(DISPLAY_NAME)
    app.setQuitOnLastWindowClosed(False)
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_NAME)
    except Exception:
        pass
    shared = QSharedMemory(APP_NAME + "_single_instance")
    if not shared.create(1):
        sys.exit(0)
    win = MainWindow()
    if "--tray" not in sys.argv:
        win.show()
    code = app.exec_()
    shared.detach()
    sys.exit(code)


if __name__ == "__main__":
    main()
