"""Main window for the refactored desktop GUI."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from PyQt6.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, pyqtProperty, QRect, QRectF
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QFont, QRegion

from .components import SidebarNavButton, SidebarStatusPanel, StatusChip, blend, rgba

# BotRunner is imported lazily to avoid discord import at module load time
def _get_bot_runner_class():
    from .bot_runner import BotRunner
    return BotRunner

# \u2500\u2500 Window control button \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class _WinBtn(QPushButton):
    """
    Rounded-square window-control button.
    Idle state uses colors.surface so it is always visible against the
    title-bar background.  Symbols are drawn with painter lines (no unicode
    glyphs) so they render crisply at any DPI.
    """

    def __init__(self, role: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        if role not in ("minimize", "close"):
            raise ValueError(f"_WinBtn: invalid role {role!r}, expected 'minimize' or 'close'")
        self._role = role
        self._hovered = False
        self._pressed = False
        # Sane defaults; overwritten on first refresh_theme call
        self._idle_bg = "#3F3F46"
        self._idle_fg = "#A1A1AA"
        self._hover_bg = "#52525B"
        self._hover_fg = "#FAFAFA"
        self._press_bg = "#27272A"
        self._press_fg = "#FFFFFF"
        self._corner_radius = 7.0
        self.setFixedSize(30, 30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlat(True)
        self.setObjectName(f"winBtn_{role}")

    def set_colors(
        self,
        idle_bg: str,
        idle_fg: str,
        hover_bg: str,
        hover_fg: str,
        press_bg: Optional[str] = None,
        press_fg: Optional[str] = None,
    ) -> None:
        self._idle_bg, self._idle_fg = idle_bg, idle_fg
        self._hover_bg, self._hover_fg = hover_bg, hover_fg
        self._press_bg = press_bg or hover_bg
        self._press_fg = press_fg or hover_fg
        self.update()

    def enterEvent(self, e):
        self._hovered = True
        self.update()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hovered = False
        self._pressed = False
        self.update()
        super().leaveEvent(e)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = True
            self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self._pressed = False
        self.update()
        super().mouseReleaseEvent(event)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._pressed:
            bg_col, fg_col = QColor(self._press_bg), QColor(self._press_fg)
        elif self._hovered:
            bg_col, fg_col = QColor(self._hover_bg), QColor(self._hover_fg)
        else:
            bg_col, fg_col = QColor(self._idle_bg), QColor(self._idle_fg)

        rect = QRectF(1.0, 1.0, self.width() - 2.0, self.height() - 2.0)
        path = QPainterPath()
        path.addRoundedRect(rect, self._corner_radius, self._corner_radius)
        p.fillPath(path, bg_col)
        outline = QColor(fg_col)
        outline.setAlpha(34)
        p.setPen(outline)
        p.drawPath(path)

        cx, cy = self.width() / 2.0, self.height() / 2.0
        pen = p.pen()
        pen.setColor(fg_col)
        pen.setWidthF(1.9)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)

        if self._role == "minimize":
            p.drawLine(int(cx - 4), int(cy + 1), int(cx + 4), int(cy + 1))
        else:
            p.drawLine(int(cx - 3), int(cy - 3), int(cx + 3), int(cy + 3))
            p.drawLine(int(cx + 3), int(cy - 3), int(cx - 3), int(cy + 3))

        p.end()


# \u2500\u2500 Custom title bar \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class TitleBar(QWidget):
    """
    Custom title bar layout:
      [ABUSER]  \u2500stretch\u2500  [current page]  \u2500stretch\u2500  [\u2500] [\u00d7]  8px
    Drag anywhere non-button to move window.
    """

    FIXED_HEIGHT = 46

    def __init__(self, window: QMainWindow, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._window  = window
        self._drag_pos: Optional[QPoint] = None
        self.setObjectName("titleBar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(self.FIXED_HEIGHT)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 0, 10, 0)
        layout.setSpacing(0)

        self.title_label = QLabel("ABUSER")
        self.title_label.setObjectName("titleBarBrand")
        tf = QFont("Segoe UI", 12)
        tf.setWeight(QFont.Weight.Bold)
        tf.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2.5)
        self.title_label.setFont(tf)
        layout.addWidget(self.title_label)

        layout.addStretch(1)

        # Right: minimize + close
        self.minimize_btn = _WinBtn("minimize")
        self.close_btn    = _WinBtn("close")
        self.minimize_btn.clicked.connect(window.showMinimized)
        self.close_btn.clicked.connect(window.close)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.addWidget(self.minimize_btn)
        btn_row.addWidget(self.close_btn)
        layout.addLayout(btn_row)

    def set_page(self, name: str) -> None:
        pass  # page label removed — no centre text


    def refresh_theme(self, colors) -> None:
        bar_top = blend(colors.bg_tertiary, colors.accent_primary, 0.42)
        bar_bottom = blend(colors.bg_secondary, colors.accent_primary, 0.30)
        border = blend(colors.border_light, colors.accent_primary, 0.44)
        self.setStyleSheet(
            f"QWidget#titleBar {{"
            f"  background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {bar_top}, stop:1 {bar_bottom});"
            f"  border-bottom: 1px solid {rgba(border, 0.98)};"
            f"}}"
        )
        self.title_label.setStyleSheet(
            f"color: {colors.text_primary}; background: transparent;")
        minimize_idle = blend(colors.surface, colors.accent_primary, 0.06)
        minimize_hover = blend(colors.surface_hover, colors.accent_primary, 0.10)
        minimize_press = blend(minimize_hover, colors.bg_primary, 0.22)
        self.minimize_btn.set_colors(
            idle_bg=minimize_idle,
            idle_fg=colors.text_secondary,
            hover_bg=minimize_hover,
            hover_fg=colors.text_primary,
            press_bg=minimize_press,
            press_fg=colors.text_primary,
        )

        close_idle = blend(colors.surface, colors.accent_primary, 0.10)
        close_hover = blend(colors.error, colors.accent_primary, 0.18)
        close_press = blend(colors.error_hover, colors.bg_primary, 0.12)
        self.close_btn.set_colors(
            idle_bg=close_idle,
            idle_fg=blend(colors.text_primary, colors.error, 0.22),
            hover_bg=close_hover,
            hover_fg="#FFFFFF",
            press_bg=close_press,
            press_fg="#FFFFFF",
        )

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = (event.globalPosition().toPoint()
                              - self._window.frameGeometry().topLeft())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._drag_pos is not None and event.buttons() == Qt.MouseButton.LeftButton:
            self._window.move(event.globalPosition().toPoint() - self._drag_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        pass  # window is fixed size


# ── Rounded window shell ──────────────────────────────────────────────────────

class _RoundedShell(QWidget):
    """
    Central widget that paints a rounded-rect background and clips all
    children to that same shape, giving the window its rounded corners.
    Radius is intentionally subtle (10 px).
    """

    RADIUS = 10

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._bg_color = QColor("#18181B")
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        self.setObjectName("roundedShell")

    def set_bg(self, hex_color: str) -> None:
        self._bg_color = QColor(hex_color)
        self.update()
        self._apply_mask()

    def _apply_mask(self) -> None:
        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            return
        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h, self.RADIUS, self.RADIUS)
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))

    def resizeEvent(self, event) -> None:
        self._apply_mask()
        super().resizeEvent(event)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(self._bg_color)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(self.rect(), self.RADIUS, self.RADIUS)
        p.end()


class CollapseButton(QPushButton):
    """A modern animated collapse toggle button with chevron icon."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._arrow_rotation = 0.0
        self._hover_progress = 0.0
        self._pressed = False
        self._compact = False
        self.setFixedSize(92, 32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(True)
        self.setFlat(True)
        self.setObjectName("collapseBtn")
        self.setStyleSheet("QPushButton#collapseBtn { min-width: 0; background: transparent; border: none; }")
        
        # Animation for rotation
        self._anim = QPropertyAnimation(self, b"arrow_rotation")
        self._anim.setDuration(200)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        
    @pyqtProperty(float)
    def arrow_rotation(self):
        return self._arrow_rotation
        
    @arrow_rotation.setter
    def arrow_rotation(self, value):
        self._arrow_rotation = value
        self.update()
        
    def set_collapsed(self, collapsed: bool):
        """Animate to collapsed or expanded state."""
        target = 180.0 if collapsed else 0.0
        self._anim.setStartValue(self._arrow_rotation)
        self._anim.setEndValue(target)
        self._anim.start()
        self.setChecked(collapsed)

    def set_compact(self, compact: bool) -> None:
        """Shrink the control when the sidebar is collapsed."""
        self._compact = compact
        if compact:
            self.setFixedSize(40, 32)
        else:
            self.setFixedSize(92, 32)
        self.update()
        
    def enterEvent(self, event):
        self._hover_progress = 1.0
        self.update()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self._hover_progress = 0.0
        self._pressed = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = True
            self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self._pressed = False
        self.update()
        super().mouseReleaseEvent(event)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        colors = getattr(self.parent(), '_collapse_colors', {})
        bg_color = QColor(colors.get('bg', '#2b2d31'))
        bg_hover = QColor(colors.get('bg_hover', '#35373c'))
        bg_active = QColor(colors.get('bg_active', '#4b2a2a'))
        bg_active_hover = QColor(colors.get('bg_active_hover', '#5c3030'))
        bg_pressed = QColor(colors.get('bg_pressed', '#241818'))
        border_color = QColor(colors.get('border', '#1e1f22'))
        border_hover = QColor(colors.get('border_hover', '#35373c'))
        border_active = QColor(colors.get('border_active', '#8f3d3d'))
        arrow_color = QColor(colors.get('arrow', '#949ba4'))
        arrow_hover = QColor(colors.get('arrow_hover', '#dbdee1'))
        arrow_active = QColor(colors.get('arrow_active', '#ffffff'))

        if self.isChecked():
            base_bg = bg_active
            hover_bg = bg_active_hover
            base_border = border_active
            base_arrow = arrow_active
        else:
            base_bg = bg_color
            hover_bg = bg_hover
            base_border = border_color
            base_arrow = arrow_color

        bg = self._interpolate_color(base_bg, hover_bg, self._hover_progress)
        border = self._interpolate_color(base_border, border_hover, self._hover_progress)
        arrow = self._interpolate_color(base_arrow, arrow_hover, self._hover_progress)
        if self._pressed:
            bg = self._interpolate_color(bg, bg_pressed, 0.35 if not self.isChecked() else 1.0)

        r = self.rect().adjusted(2, 2, -2, -2)
        rect = QRectF(r.x(), r.y(), r.width(), r.height())
        path = QPainterPath()
        path.addRoundedRect(rect, 10, 10)
        
        painter.fillPath(path, bg)
        painter.setPen(QColor(border))
        painter.drawPath(path)

        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self._arrow_rotation)
        self._draw_chevron(painter, arrow)
        painter.end()
        
    def _interpolate_color(self, c1: QColor, c2: QColor, t: float) -> QColor:
        """Interpolate between two colors."""
        return QColor(
            int(c1.red() + (c2.red() - c1.red()) * t),
            int(c1.green() + (c2.green() - c1.green()) * t),
            int(c1.blue() + (c2.blue() - c1.blue()) * t),
            int(c1.alpha() + (c2.alpha() - c1.alpha()) * t),
        )
        
    def _draw_chevron(self, painter: QPainter, arrow_color: QColor = None):
        """Draw a chevron arrow pointing right."""
        size = 8
        x_offset = 1  # Slight offset for visual balance
        
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Use the provided arrow color or current pen
        pen = painter.pen()
        if arrow_color:
            pen.setColor(arrow_color)
        pen.setWidth(2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        
        # Draw > shape
        half = size / 2
        painter.drawLine(int(-half + x_offset), int(-half), int(half + x_offset), 0)
        painter.drawLine(int(-half + x_offset), int(half), int(half + x_offset), 0)
from .config import load_gui_config, save_gui_config, update_last_route
from .pages import DMPage, DocsPage, GuildItem, GuildsPage, JoinerPage, BoosterPage, LoginPage, LogsPage, NukerPage, SettingsPage
from .routes import (
    ROUTE_BOOSTER,
    ROUTE_DOCS,
    ROUTE_DM,
    ROUTE_GUILDS,
    ROUTE_JOINER,
    ROUTE_LABELS,
    ROUTE_LAST_USED,
    ROUTE_LOGIN,
    ROUTE_LOGS,
    ROUTE_NUKER,
    ROUTE_SETTINGS,
    ROUTES,
    get_route_index,
    normalize_route,
    route_from_label,
)
from .theme import get_theme_manager


class MainWindow(QMainWindow):
    """Main application window for the desktop GUI."""

    WINDOW_W = 1280
    WINDOW_H = 820

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ABUSER")

        # ── Frameless + fixed size + rounded corners ─────────────────────────
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Window
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(self.WINDOW_W, self.WINDOW_H)

        self.theme_manager = get_theme_manager()
        self.theme_manager.set_theme_changed_callback(self._on_theme_changed)

        self.bot_runner: Optional["BotRunner"] = None
        self._current_route = ROUTE_LOGIN
        self._config = load_gui_config()
        self._sidebar_connected = False

        self._build_ui()
        self._set_sidebar_connection_state(False)
        self._connect_page_signals()
        self.refresh_theme()
        # REMOVED: self.switch_route(ROUTE_LOGIN, persist=False)
        # load_and_apply_settings() called in main.py handles this

    def _build_ui(self) -> None:
        # _RoundedShell paints the bg + clips children to rounded rect
        self._shell = _RoundedShell()
        self._shell.setObjectName("mainShell")
        self.setCentralWidget(self._shell)

        root = QVBoxLayout(self._shell)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Custom title bar (spans full width above sidebar+content) ─────────
        self.title_bar = TitleBar(self)
        root.addWidget(self.title_bar)

        # ── Body: sidebar + content side-by-side ──────────────────────────────
        body = QWidget()
        body.setObjectName("bodyShell")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        root.addWidget(body, 1)

        self.sidebar = self._build_sidebar()
        body_layout.addWidget(self.sidebar)

        self.content_shell = QWidget()
        self.content_shell.setObjectName("contentShell")
        self.content_layout = QVBoxLayout(self.content_shell)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        body_layout.addWidget(self.content_shell, 1)

        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("contentStack")
        self.content_layout.addWidget(self.content_stack, 1)

        self.login_tab = LoginPage()
        self.docs_tab = DocsPage()
        self.guilds_tab = GuildsPage()
        self.nuker_tab = NukerPage()
        self.dm_tab = DMPage()
        self.joiner_tab = JoinerPage()
        self.booster_tab = BoosterPage()
        self.logs_tab = LogsPage()
        self.settings_tab = SettingsPage()

        self.pages = {
            ROUTE_LOGIN:    self.login_tab,
            ROUTE_GUILDS:   self.guilds_tab,
            ROUTE_NUKER:    self.nuker_tab,
            ROUTE_DM:       self.dm_tab,
            ROUTE_JOINER:   self.joiner_tab,
            ROUTE_BOOSTER:  self.booster_tab,
            ROUTE_LOGS:     self.logs_tab,
            ROUTE_SETTINGS: self.settings_tab,
            ROUTE_DOCS:     self.docs_tab,
        }

        for route in ROUTES:
            self.content_stack.addWidget(self.pages[route.key])

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebarShell")
        sidebar.setFixedWidth(self.theme_manager.tokens.metrics.sidebar_width)

        self._sidebar_expanded_margins = (10, 18, 10, 12)
        self._sidebar_collapsed_margins = (14, 18, 14, 12)
        self._sidebar_layout = QVBoxLayout(sidebar)
        self._sidebar_layout.setContentsMargins(*self._sidebar_expanded_margins)
        self._sidebar_layout.setSpacing(4)

        # ── Brand ────────────────────────────────────────────────────────────
        self._brand_widget = QWidget()
        self._brand_widget.setVisible(False)
        self.brand_title = QLabel("ABUSER")
        self.brand_meta = QLabel("Discord SelfBot | v1.5")

        # ── Nav heading + collapse button ─────────────────────────────────────
        self._nav_heading_widget = QWidget()
        nav_heading_layout = QHBoxLayout(self._nav_heading_widget)
        nav_heading_layout.setContentsMargins(6, 8, 0, 4)
        nav_heading_layout.setSpacing(0)
        self.nav_heading = QLabel("NAVIGATION")
        nav_heading_layout.addWidget(self.nav_heading)
        nav_heading_layout.addStretch(1)

        self._sidebar_collapsed = False
        self._collapse_btn = CollapseButton()
        self._collapse_btn.clicked.connect(self._toggle_sidebar)
        self._collapse_btn.set_compact(False)
        nav_heading_layout.addWidget(self._collapse_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        self._sidebar_layout.addWidget(self._nav_heading_widget)

        # ── Nav buttons ───────────────────────────────────────────────────────
        self.route_buttons: dict[str, SidebarNavButton] = {}
        self._sidebar_dividers: list[QFrame] = []
        prev_group: str | None = None
        for route in ROUTES:
            if prev_group is not None and route.group != prev_group:
                divider = QFrame()
                divider.setObjectName("sidebarDivider")
                divider.setFrameShape(QFrame.Shape.HLine)
                divider.setFixedHeight(1)
                self._sidebar_layout.addWidget(divider)
                self._sidebar_dividers.append(divider)
            prev_group = route.group
            button = SidebarNavButton(route.icon_name, route.label)
            button.clicked.connect(lambda checked=False, key=route.key: self.switch_route(key))
            self._sidebar_layout.addWidget(button)
            self.route_buttons[route.key] = button

        self._sidebar_layout.addStretch(1)

        # ── Status panel ──────────────────────────────────────────────────────
        self.status_panel = SidebarStatusPanel()
        self._sidebar_layout.addWidget(self.status_panel)

        self.sidebar_status_pill = StatusChip("Offline", "danger")
        self.sidebar_status_pill.setVisible(False)
        self._sidebar_layout.addWidget(self.sidebar_status_pill, 0, Qt.AlignmentFlag.AlignHCenter)

        return sidebar

    def _toggle_sidebar(self) -> None:
        """Collapse to icon-only rail or expand back to full sidebar."""
        self._sidebar_collapsed = not self._sidebar_collapsed
        expanded_width = self.theme_manager.tokens.metrics.sidebar_width
        COLLAPSED_W = 84

        # Animate button rotation
        self._collapse_btn.set_collapsed(self._sidebar_collapsed)
        
        if self._sidebar_collapsed:
            self.sidebar.setFixedWidth(COLLAPSED_W)
            self._sidebar_layout.setContentsMargins(*self._sidebar_collapsed_margins)
            self._collapse_btn.set_compact(True)
            self._brand_widget.setVisible(False)
            self.nav_heading.setVisible(False)
            self._sidebar_layout.setAlignment(self._nav_heading_widget, Qt.AlignmentFlag.AlignHCenter)
            for btn in self.route_buttons.values():
                btn.set_collapsed(True)
                self._sidebar_layout.setAlignment(btn, Qt.AlignmentFlag.AlignHCenter)
            for div in self._sidebar_dividers:
                div.setVisible(False)
            self.status_panel.setVisible(False)
            self.sidebar_status_pill.setVisible(True)
        else:
            self.sidebar.setFixedWidth(expanded_width)
            self._sidebar_layout.setContentsMargins(*self._sidebar_expanded_margins)
            self._collapse_btn.set_compact(False)
            self._brand_widget.setVisible(False)
            self.nav_heading.setVisible(True)
            self._sidebar_layout.setAlignment(self._nav_heading_widget, Qt.AlignmentFlag(0))
            for btn in self.route_buttons.values():
                btn.set_collapsed(False)
                self._sidebar_layout.setAlignment(btn, Qt.AlignmentFlag(0))
            for div in self._sidebar_dividers:
                div.setVisible(True)
            self.status_panel.setVisible(True)
            self.sidebar_status_pill.setVisible(False)

    def _set_sidebar_connection_state(self, connected: bool) -> None:
        self._sidebar_connected = connected
        if connected:
            self.sidebar_status_pill.setText("Online")
            self.sidebar_status_pill.set_tone("success")
        else:
            self.sidebar_status_pill.setText("Offline")
            self.sidebar_status_pill.set_tone("danger")

    def _connect_page_signals(self) -> None:
        self.nuker_tab.nuke_action_requested.connect(self._on_nuke_action_requested)
        self.nuker_tab.setup_server_requested.connect(self._on_setup_server_requested)
        self.settings_tab.settings_applied.connect(self._on_settings_applied)

    def connect_bot_runner(self, bot_runner: "BotRunner") -> None:
        self.bot_runner = bot_runner

        self.login_tab.login_requested.connect(self.bot_runner.start_bot)
        self.login_tab.logout_requested.connect(self.bot_runner.stop_bot)
        self.guilds_tab.refresh_requested.connect(self.bot_runner.refresh_guilds)

        self.bot_runner.login_success.connect(self._on_login_success)
        self.bot_runner.login_failed.connect(self._on_login_failed)
        self.bot_runner.logout_completed.connect(self._on_logout_completed)
        self.bot_runner.guilds_updated.connect(self._on_guilds_updated)
        self.bot_runner.log_received.connect(self._on_log_received)
        self.bot_runner.status_changed.connect(self._on_status_changed)
        self.bot_runner.connection_state_changed.connect(self._on_connection_state_changed)
        self.bot_runner.latency_updated.connect(self._on_latency_updated)
        self.bot_runner.nuke_action_completed.connect(self.nuker_tab.on_action_completed)
        self.bot_runner.setup_server_completed.connect(self.nuker_tab.on_setup_completed)

    def switch_ui_theme(self, theme_name: str, accent: Optional[str] = None):
        return self.theme_manager.switch_theme(theme_name, accent)

    def get_available_themes(self):
        return self.theme_manager.get_available_themes()

    def get_available_accents(self):
        return self.theme_manager.get_available_accents()

    def switch_tab(self, index: int):
        if 0 <= index < len(ROUTES):
            self.switch_route(ROUTES[index].key)

    def switch_route(self, route_key: str, persist: bool = True) -> None:
        route_key = normalize_route(route_key)
        self._current_route = route_key
        self.content_stack.setCurrentIndex(get_route_index(route_key))

        for key, button in self.route_buttons.items():
            button.setChecked(key == route_key)
            button.refresh_theme()

        self.title_bar.set_page(ROUTE_LABELS.get(route_key, ""))
        if persist:
            update_last_route(route_key)

    def _status_tone(self, message: str) -> str:
        message = message.lower()
        if "ready" in message or "connected" in message:
            return "success"
        if "error" in message or "fail" in message:
            return "danger"
        if "starting" in message or "connecting" in message or "stopping" in message:
            return "warning"
        return "neutral"

    def _on_login_success(self, user_name: str, _user_id: str) -> None:
        token = self.login_tab.token_input.text().strip()
        self.login_tab.save_token_if_requested(token, user_name)
        self.login_tab.on_login_success(user_name)
        self._set_sidebar_connection_state(True)
        self.status_panel.set_connection_state(True, user_name, f"Ready as {user_name}")
        self.guilds_tab.set_connected(True, user_name)
        self.nuker_tab.set_connected(True)
        self.switch_route(ROUTE_GUILDS)

    def _on_login_failed(self, error_message: str) -> None:
        self.login_tab.show_error(error_message)
        self._set_sidebar_connection_state(False)
        self.status_panel.set_connection_state(False, message=error_message)
        self.switch_route(ROUTE_LOGIN)

    def _on_logout_completed(self) -> None:
        self.login_tab.on_logout()
        self._set_sidebar_connection_state(False)
        self.guilds_tab.set_connected(False)
        self.nuker_tab.set_connected(False)
        self.nuker_tab.set_selected_guild(None)
        self.status_panel.set_connection_state(False)
        self.switch_route(ROUTE_LOGIN)

    def _on_guilds_updated(self, guild_list: list[dict]) -> None:
        from datetime import datetime
        guilds: list[GuildItem] = []
        for guild in guild_list:
            # Parse created_at from ISO format if present
            created_at = None
            if guild.get("created_at"):
                try:
                    created_at = datetime.fromisoformat(guild["created_at"])
                except (ValueError, TypeError):
                    pass
            
            is_owner_val = guild.get("is_owner", False)

            item = GuildItem(
                guild_id=int(guild["id"]),
                name=guild["name"],
                member_count=guild.get("member_count", 0) or 0,
                icon_url=guild.get("icon_url"),
                owner_id=int(guild["owner_id"]) if guild.get("owner_id") else None,
                created_at=created_at,
                channels_count=guild.get("channels_count", 0) or 0,
                roles_count=guild.get("roles_count", 0) or 0,
                boost_count=guild.get("boost_count", 0) or 0,
                my_permissions=guild.get("my_permissions", 0) or 0,
                is_owner=is_owner_val,
                icon_data=guild.get("icon_data"),  # Pass icon bytes to UI
            )
            guilds.append(item)
        self.guilds_tab.update_guilds(guilds)
        self.nuker_tab.update_guild_list(guilds)
        self.status_panel.set_guild_count(len(guilds))

    def _on_log_received(self, level: str, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        name = "Bot"
        parsed_level = level.upper()
        parsed_message = message

        parts = message.split(" - ", 3)
        if len(parts) == 4:
            timestamp, name, parsed_level, parsed_message = parts

        self.logs_tab.add_log(timestamp, name, parsed_level, parsed_message)

    def _on_status_changed(self, message: str) -> None:
        tone = self._status_tone(message)
        self.status_panel.set_status_message(message, tone)
        if tone == "success" and self.bot_runner and self.bot_runner.user_name:
            self.status_panel.set_connection_state(True, self.bot_runner.user_name, message)

    def _on_connection_state_changed(self, is_connected: bool) -> None:
        if not is_connected and self.bot_runner and not self.bot_runner.is_running:
            self._set_sidebar_connection_state(False)
            self.status_panel.set_connection_state(False)
            self.guilds_tab.set_connected(False)

    def _on_latency_updated(self, ping_ms: float) -> None:
        self.status_panel.set_ping(ping_ms)

    def _on_nuke_requested(self, guild) -> None:
        """Handle nuke button click from Guilds page - switch to Nuker with guild pre-selected."""
        # Switch to Nuker tab with the guild pre-selected
        self.nuker_tab.set_selected_guild(guild)
        self.switch_route(ROUTE_NUKER)
    
    def _on_nuke_action_requested(self, action_id: str, guild_id_str: str) -> None:
        """Handle nuke action request from Nuker page."""
        # Convert guild_id from string to int (passed as string to avoid 32-bit truncation)
        guild_id = int(guild_id_str)
        
        if not self.bot_runner:
            QMessageBox.warning(self, "Error", "Bot runner not available.")
            return
        
        if not self.bot_runner.is_connected:
            QMessageBox.warning(self, "Not Connected", "Please connect to Discord first.")
            return
        
        # Verify the guild exists in the bot's guild list
        available_guild_ids = [g.guild_id for g in self.guilds_tab._guilds.values()] if hasattr(self.guilds_tab, '_guilds') else []
        
        if guild_id not in available_guild_ids:
            QMessageBox.warning(
                self, 
                "Guild Not Available", 
                f"Guild {guild_id} is not in the list of available guilds.\n\n"
                f"Available guilds: {available_guild_ids}\n\n"
                f"Please select a different guild from the Guilds tab."
            )
            return
        
        # Execute the action through the bot runner
        success = self.bot_runner.execute_nuke_action(action_id, guild_id)
        if not success:
            self.nuker_tab.on_action_completed(action_id, False, "Failed to queue action")

    def _on_setup_server_requested(self, guild_id_str: str, server_name: str, roles_count: int, channels_count: int) -> None:
        """Handle setup server request from Nuker page."""
        # Convert guild_id from string to int (passed as string to avoid 32-bit truncation)
        guild_id = int(guild_id_str)
        
        if not self.bot_runner:
            QMessageBox.warning(self, "Error", "Bot runner not available.")
            return
        
        if not self.bot_runner.is_connected:
            QMessageBox.warning(self, "Not Connected", "Please connect to Discord first.")
            return
        
        # Verify the guild exists in the bot's guild list
        available_guild_ids = [g.guild_id for g in self.guilds_tab._guilds.values()] if hasattr(self.guilds_tab, '_guilds') else []
        if guild_id not in available_guild_ids:
            QMessageBox.warning(
                self, 
                "Guild Not Available", 
                f"Guild {guild_id} is not in the list of available guilds.\n\n"
                f"Please select a guild from the Guilds tab first."
            )
            return
        
        # Execute the setup through the bot runner with parameters
        success = self.bot_runner.execute_setup_server(guild_id, server_name, roles_count, channels_count)
        if not success:
            self.nuker_tab.on_setup_completed(False, "Failed to queue setup action")

    def _on_settings_applied(self, config: dict) -> None:
        self._config = config
        save_gui_config(config)
        self.apply_settings(config)

    def apply_settings(self, config: dict) -> None:
        self._config = config
        appearance = config.get("appearance", {})

        preset = appearance.get("preset", "Discord Dark")
        # Normalise label → enum key; "Blurple" is our friendly name for Discord Blue
        _ACCENT_LABEL_MAP = {
            "blurple":      "discord_blue",
            "discord blue": "discord_blue",
            "discord_blue": "discord_blue",
            "red":          "red",
            "green":        "green",
            "pink":         "pink",
            "cyan":         "cyan",
        }
        raw = appearance.get("accent", "Blurple").lower().replace(" ", "_")
        accent = _ACCENT_LABEL_MAP.get(raw, raw)
        self.theme_manager.switch_theme(preset, accent)
        self.theme_manager.save_theme()

        app = QApplication.instance()
        if app:
            font = app.font()
            font.setPointSize(appearance.get("font_size", 13))
            app.setFont(font)
            self.theme_manager.apply_theme(app)

        self.login_tab.set_privacy_options(config.get("privacy", {}).get("save_tokens", True))
        if not self.login_tab.is_connected:
            self.login_tab.load_saved_tokens()
        self.settings_tab.load_from_config(config)
        self.refresh_theme()

    def load_and_apply_settings(self) -> None:
        self._config = load_gui_config()
        self.apply_settings(self._config)

        startup_label = self._config.get("behavior", {}).get("startup_page", "Login")
        if startup_label == "Last Used":
            route_key = normalize_route(self._config.get("behavior", {}).get("last_route", ROUTE_LOGIN))
        else:
            route_key = route_from_label(startup_label)
        self.switch_route(route_key, persist=False)

    def _on_theme_changed(self, _theme) -> None:
        self.refresh_theme()

    def refresh_theme(self) -> None:
        colors = self.theme_manager.tokens.colors

        # Paint rounded shell with the deepest bg colour
        if hasattr(self, "_shell"):
            self._shell.set_bg(colors.bg_primary)

        self.setStyleSheet(f"QMainWindow {{ background: transparent; }}")

        self.sidebar.setStyleSheet(
            f"""
            QFrame#sidebarShell {{
                background-color: {colors.bg_secondary};
                border-right: 1px solid {rgba(colors.border_light, 0.9)};
            }}
            """
        )
        self.sidebar.setGraphicsEffect(None)
        self.brand_title.setStyleSheet(
            f"color: {colors.text_primary}; font-size: 18px; font-weight: 700; letter-spacing: 2px;"
        )
        self.nav_heading.setStyleSheet(
            f"color: {colors.text_muted}; font-size: 10px; font-weight: 700; letter-spacing: 1.4px;"
        )

        self.title_bar.refresh_theme(colors)
        self.content_shell.setStyleSheet(f"QWidget#contentShell {{ background-color: {colors.bg_primary}; }}")
        self.content_stack.setStyleSheet(f"QStackedWidget#contentStack {{ background-color: {colors.bg_primary}; }}")

        for button in self.route_buttons.values():
            button.refresh_theme()

        self.status_panel.refresh_theme()
        for page in self.pages.values():
            refresh = getattr(page, "refresh_theme", None)
            if callable(refresh):
                refresh()

        tm = self.theme_manager.theme
        for div in self._sidebar_dividers:
            div.setStyleSheet(f"background-color: {tm.divider}; border: none;")

        # Update collapse button theme colors for custom painting
        if hasattr(self, "_collapse_btn"):
            collapse_bg = blend(tm.surface, tm.accent_primary, 0.08)
            collapse_hover = blend(tm.surface_hover, tm.accent_primary, 0.18)
            collapse_active = blend(tm.surface, tm.accent_primary, 0.38)
            collapse_active_hover = blend(tm.surface_hover, tm.accent_primary, 0.46)
            self._collapse_colors = {
                'bg': collapse_bg,
                'bg_hover': collapse_hover,
                'bg_active': collapse_active,
                'bg_active_hover': collapse_active_hover,
                'bg_pressed': blend(tm.bg_primary, tm.accent_primary, 0.22),
                'border': rgba(tm.border_light, 0.55),
                'border_hover': rgba(blend(tm.border_light, tm.accent_primary, 0.25), 0.95),
                'border_active': rgba(blend(tm.accent_primary, tm.border_light, 0.25), 0.98),
                'arrow': tm.text_secondary,
                'arrow_hover': tm.text_primary,
                'arrow_active': "#FFFFFF",
            }
            self._collapse_btn._collapse_colors = self._collapse_colors
            self._collapse_btn.update()
