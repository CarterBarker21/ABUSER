"""Shared themed widgets for the desktop GUI."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtGui import QFont, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .theme import DesignTokens, get_theme_manager


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    color = color.lstrip("#")
    return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)


def rgba(color: str, alpha: float) -> str:
    red, green, blue = _hex_to_rgb(color)
    alpha = max(0.0, min(1.0, alpha))
    return f"rgba({red}, {green}, {blue}, {alpha:.3f})"


def blend(color_a: str, color_b: str, weight: float) -> str:
    weight = max(0.0, min(1.0, weight))
    ar, ag, ab = _hex_to_rgb(color_a)
    br, bg, bb = _hex_to_rgb(color_b)
    red = round(ar + (br - ar) * weight)
    green = round(ag + (bg - ag) * weight)
    blue = round(ab + (bb - ab) * weight)
    return f"#{red:02X}{green:02X}{blue:02X}"


def refresh_themed_tree(widget: QWidget) -> None:
    for child in widget.findChildren(QWidget):
        if child is widget:
            continue
        refresh = getattr(child, "refresh_theme", None)
        if callable(refresh):
            refresh()


class ThemedWidget:
    """Mixin for widgets that read tokens from ThemeManager."""

    @property
    def theme(self):
        return get_theme_manager().theme

    @property
    def tokens(self):
        return get_theme_manager().tokens

    @property
    def dt(self) -> DesignTokens:
        """Semantic design tokens — use this instead of raw ``self.theme`` in new code."""
        return get_theme_manager().design_tokens

    def refresh_theme(self) -> None:  # pragma: no cover - interface hook
        pass


class StatusChip(QLabel, ThemedWidget):
    def __init__(self, text: str = "", tone: str = "neutral", parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self._tone = tone
        self.setObjectName("statusChip")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.refresh_theme()

    def set_tone(self, tone: str) -> None:
        self._tone = tone
        self.refresh_theme()

    def refresh_theme(self) -> None:
        dt = self.dt
        palette = {
            "neutral":  (rgba(dt.text_secondary, 0.14), dt.text_secondary,  rgba(dt.border_strong, 0.9)),
            "accent":   (rgba(dt.accent, 0.16),         dt.accent,           rgba(dt.accent, 0.42)),
            "success":  (rgba(dt.success_bright, 0.16), dt.success_bright,   rgba(dt.success_bright, 0.42)),
            "warning":  (rgba(dt.warning, 0.16),        dt.warning,          rgba(dt.warning, 0.42)),
            "danger":   (rgba(dt.danger, 0.16),         dt.danger,           rgba(dt.danger, 0.42)),
            "preview":  (rgba(dt.text_muted, 0.14),     dt.text_muted,       rgba(dt.text_muted, 0.36)),
        }
        background, text, border = palette.get(self._tone, palette["neutral"])
        radius = self.tokens.metrics.control_height_sm // 2
        self.setStyleSheet(
            f"""
            QLabel#statusChip {{
                background-color: {background};
                color: {text};
                border: 1px solid {border};
                border-radius: {radius}px;
                padding: 4px 10px;
                font-size: 10px;
                font-weight: 600;
            }}
            """
        )


class PageHeader(QWidget, ThemedWidget):
    def __init__(self, title: str, description: str = "", eyebrow: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._title = title
        self._description = description
        self._eyebrow = eyebrow

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(12)
        layout.addLayout(top_row)

        text_column = QVBoxLayout()
        text_column.setContentsMargins(0, 0, 0, 0)
        text_column.setSpacing(6)
        top_row.addLayout(text_column, 1)

        self.eyebrow_label = QLabel(eyebrow.upper())
        self.eyebrow_label.setVisible(bool(eyebrow))
        text_column.addWidget(self.eyebrow_label)

        self.title_label = QLabel(title)
        title_font = QFont("Segoe UI", 22)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        text_column.addWidget(self.title_label)

        self.description_label = QLabel(description)
        self.description_label.setWordWrap(True)
        self.description_label.setVisible(bool(description))
        text_column.addWidget(self.description_label)

        self.status_chip = StatusChip("")
        self.status_chip.setVisible(False)
        top_row.addWidget(self.status_chip, 0, Qt.AlignmentFlag.AlignTop)

        self.refresh_theme()

    def set_status(self, text: str = "", tone: str = "neutral") -> None:
        self.status_chip.setText(text)
        self.status_chip.set_tone(tone)
        self.status_chip.setVisible(bool(text))

    def refresh_theme(self) -> None:
        dt = self.dt
        self.eyebrow_label.setStyleSheet(
            f"color: {dt.text_muted}; font-size: 11px; font-weight: 700; letter-spacing: 1.8px;"
        )
        self.title_label.setStyleSheet(f"color: {dt.text_primary};")
        self.description_label.setStyleSheet(
            f"color: {dt.text_secondary}; font-size: 13px; line-height: 1.4em;"
        )
        self.status_chip.refresh_theme()


class SectionLabel(QLabel, ThemedWidget):
    def __init__(self, text: str, parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self.refresh_theme()

    def refresh_theme(self) -> None:
        dt = self.dt
        self.setStyleSheet(
            f"color: {dt.text_muted}; font-size: 11px; font-weight: 700; letter-spacing: 1px;"
        )


class PanelCard(QFrame, ThemedWidget):
    def __init__(
        self,
        title: str = "",
        description: str = "",
        parent: Optional[QWidget] = None,
        tone: str = "neutral",
    ):
        super().__init__(parent)
        self._tone = tone
        self.setObjectName("panelCard")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 18, 18, 18)
        outer.setSpacing(14)

        self.header_widget = QWidget()
        header_layout = QVBoxLayout(self.header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(4)
        outer.addWidget(self.header_widget)

        self.title_label = QLabel(title)
        title_font = QFont("Segoe UI", 12)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        header_layout.addWidget(self.title_label)

        self.description_label = QLabel(description)
        self.description_label.setWordWrap(True)
        self.description_label.setVisible(bool(description))
        header_layout.addWidget(self.description_label)

        self.body_layout = QVBoxLayout()
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(14)
        outer.addLayout(self.body_layout)

        self.refresh_theme()

    def refresh_theme(self) -> None:
        dt = self.dt
        border_map = {
            "neutral": rgba(dt.border_strong, 0.9),
            "accent":  rgba(dt.accent, 0.45),
            "warning": rgba(dt.warning, 0.48),
            "danger":  rgba(dt.danger, 0.48),
            "success": rgba(dt.success_bright, 0.48),
        }
        border = border_map.get(self._tone, border_map["neutral"])
        self.setStyleSheet(
            f"""
            QFrame#panelCard {{
                background-color: {dt.surface};
                border: 1px solid {border};
                border-radius: {self.tokens.metrics.card_radius}px;
            }}
            """
        )
        self.title_label.setStyleSheet(f"color: {dt.text_primary};")
        self.description_label.setStyleSheet(
            f"color: {dt.text_secondary}; font-size: 12px; line-height: 1.4em;"
        )


class AppButton(QPushButton, ThemedWidget):
    def __init__(self, text: str, variant: str = "secondary", parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self._variant = variant
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(self.tokens.metrics.control_height_md)
        self.refresh_theme()

    def set_variant(self, variant: str) -> None:
        self._variant = variant
        self.refresh_theme()

    def refresh_theme(self) -> None:
        dt = self.dt
        variants = {
            "primary":   (dt.accent,                    "#FFFFFF",          dt.accent_hover,    rgba(dt.accent, 0.7)),
            "secondary": (dt.surface,                   dt.text_primary,    dt.surface_raised,  rgba(dt.border_strong, 1.0)),
            "tertiary":  (rgba(dt.surface, 0.45),       dt.text_secondary,  rgba(dt.surface_raised, 0.85), rgba(dt.border_strong, 0.8)),
            "danger":    (dt.danger,                    "#FFFFFF",          dt.danger_hover,    rgba(dt.danger, 0.6)),
            "success":   (dt.success,                   "#FFFFFF",          dt.success,         rgba(dt.success_bright, 0.6)),
            "preview":   (rgba(dt.text_muted, 0.12),    dt.text_muted,      rgba(dt.text_muted, 0.18), rgba(dt.text_muted, 0.35)),
        }
        background, text, hover, border = variants.get(self._variant, variants["secondary"])
        disabled_bg   = rgba(dt.text_muted, 0.12)
        disabled_text = blend(dt.text_muted, dt.background, 0.05)
        pressed = hover if hover.startswith("rgba") else blend(hover, dt.background, 0.18)
        self.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {background};
                color: {text};
                border: 1px solid {border};
                border-radius: 10px;
                padding: 0 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
            QPushButton:pressed {{
                background-color: {pressed};
            }}
            QPushButton:disabled {{
                background-color: {disabled_bg};
                color: {disabled_text};
                border-color: {rgba(dt.text_muted, 0.25)};
            }}
            """
        )


class SidebarNavButton(QPushButton, ThemedWidget):
    _icon_dir = Path(__file__).resolve().parent / "assets" / "icons" / "sidebar"

    def __init__(self, icon_name: str, label: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._icon_name = icon_name
        self._label = label
        self._icon_svg = self._load_icon_svg(icon_name)
        self.setObjectName("sidebarNavButton")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(44)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(10)

        self.icon_label = QLabel()
        self.icon_label.setObjectName("sidebarNavIcon")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setFixedSize(18, 18)
        layout.addWidget(self.icon_label, 0, Qt.AlignmentFlag.AlignVCenter)

        self.title_label = QLabel(label)
        self.title_label.setObjectName("sidebarNavTitle")
        title_font = QFont("Segoe UI", 10)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        layout.addWidget(self.title_label, 1)

        self.refresh_theme()

    def _load_icon_svg(self, icon_name: str) -> str:
        icon_path = self._icon_dir / f"{icon_name}.svg"
        try:
            return icon_path.read_text(encoding="utf-8")
        except OSError:
            return ""

    def _update_icon(self, color: str) -> None:
        if not self._icon_svg:
            self.icon_label.clear()
            return

        svg_data = self._icon_svg.replace("currentColor", color)
        renderer = QSvgRenderer(QByteArray(svg_data.encode("utf-8")))
        pixmap = QPixmap(18, 18)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        self.icon_label.setPixmap(pixmap)

    def refresh_theme(self) -> None:
        dt = self.dt
        self.setStyleSheet(
            f"""
            QPushButton#sidebarNavButton {{
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 12px;
                text-align: left;
            }}
            QPushButton#sidebarNavButton:hover {{
                background-color: {rgba(dt.surface_raised, 0.7)};
                border-color: {rgba(dt.border_strong, 0.7)};
            }}
            QPushButton#sidebarNavButton:checked {{
                background-color: {dt.accent_muted};
                border: 1px solid {rgba(dt.accent, 0.36)};
                border-left: 3px solid {dt.accent};
            }}
            QPushButton#sidebarNavButton:checked:hover {{
                background-color: {rgba(dt.accent, 0.2)};
            }}
            """
        )
        checked = self.isChecked()
        icon_color = dt.accent if checked else dt.text_muted
        title_fg   = dt.text_primary if checked else dt.text_secondary
        self.icon_label.setStyleSheet("background-color: transparent;")
        self._update_icon(icon_color)
        self.title_label.setStyleSheet(f"color: {title_fg}; background-color: transparent;")


class AppLineEdit(QLineEdit, ThemedWidget):
    def __init__(self, placeholder: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(self.tokens.metrics.control_height_md)
        self.refresh_theme()

    def refresh_theme(self) -> None:
        dt = self.dt
        self.setStyleSheet(
            f"""
            QLineEdit {{
                background-color: {dt.background};
                color: {dt.text_primary};
                border: 1px solid {rgba(dt.border_strong, 0.95)};
                border-radius: 10px;
                padding: 0 12px;
                selection-background-color: {rgba(dt.accent, 0.35)};
            }}
            QLineEdit:hover {{
                border-color: {rgba(dt.text_secondary, 0.6)};
            }}
            QLineEdit:focus {{
                border-color: {dt.accent};
            }}
            """
        )


class SearchField(AppLineEdit):
    pass


class AppComboBox(QComboBox, ThemedWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setMinimumHeight(self.tokens.metrics.control_height_md)
        self.refresh_theme()

    def refresh_theme(self) -> None:
        dt = self.dt
        self.setStyleSheet(
            f"""
            QComboBox {{
                background-color: {dt.background};
                color: {dt.text_primary};
                border: 1px solid {rgba(dt.border_strong, 0.95)};
                border-radius: 10px;
                padding: 0 12px;
            }}
            QComboBox:hover {{
                border-color: {rgba(dt.text_secondary, 0.6)};
            }}
            QComboBox:focus {{
                border-color: {dt.accent};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 22px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {dt.surface};
                color: {dt.text_primary};
                border: 1px solid {dt.border};
                selection-background-color: {rgba(dt.accent, 0.28)};
            }}
            """
        )


class AppTextEdit(QTextEdit, ThemedWidget):
    def __init__(self, placeholder: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.refresh_theme()

    def refresh_theme(self) -> None:
        dt = self.dt
        self.setStyleSheet(
            f"""
            QTextEdit {{
                background-color: {dt.background};
                color: {dt.text_primary};
                border: 1px solid {rgba(dt.border_strong, 0.95)};
                border-radius: 12px;
                padding: 10px 12px;
                selection-background-color: {rgba(dt.accent, 0.35)};
            }}
            QTextEdit:hover {{
                border-color: {rgba(dt.text_secondary, 0.6)};
            }}
            QTextEdit:focus {{
                border-color: {dt.accent};
            }}
            """
        )


class AppSpinBox(QSpinBox, ThemedWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setMinimumHeight(self.tokens.metrics.control_height_md)
        self.refresh_theme()

    def refresh_theme(self) -> None:
        dt = self.dt
        self.setStyleSheet(
            f"""
            QSpinBox {{
                background-color: {dt.background};
                color: {dt.text_primary};
                border: 1px solid {rgba(dt.border_strong, 0.95)};
                border-radius: 10px;
                padding: 0 12px;
            }}
            QSpinBox:hover {{
                border-color: {rgba(dt.text_secondary, 0.6)};
            }}
            QSpinBox:focus {{
                border-color: {dt.accent};
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                border: none;
                background: transparent;
                width: 16px;
            }}
            """
        )


class ToggleSwitch(QCheckBox, ThemedWidget):
    def __init__(self, text: str, parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_theme()

    def refresh_theme(self) -> None:
        dt = self.dt
        self.setStyleSheet(
            f"""
            QCheckBox {{
                color: {dt.text_primary};
                spacing: 10px;
            }}
            QCheckBox:disabled {{
                color: {dt.text_muted};
            }}
            QCheckBox::indicator {{
                width: 36px;
                height: 20px;
                border-radius: 10px;
                background-color: {rgba(dt.text_muted, 0.22)};
                border: 1px solid {rgba(dt.border_strong, 0.7)};
            }}
            QCheckBox::indicator:checked {{
                background-color: {dt.accent};
                border-color: {dt.accent};
            }}
            QCheckBox::indicator:unchecked:hover {{
                background-color: {rgba(dt.text_muted, 0.32)};
            }}
            """
        )


class InfoBanner(QFrame, ThemedWidget):
    def __init__(self, title: str, message: str, tone: str = "neutral", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._tone = tone
        self.setObjectName("infoBanner")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        self.title_label = QLabel(title)
        title_font = QFont("Segoe UI", 10)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        layout.addWidget(self.title_label)

        self.message_label = QLabel(message)
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)

        self.refresh_theme()

    def refresh_theme(self) -> None:
        dt = self.dt
        mapping = {
            "neutral": (rgba(dt.surface_raised, 0.55), rgba(dt.border_strong, 0.85), dt.text_secondary),
            "accent":  (rgba(dt.accent, 0.12),         rgba(dt.accent, 0.35),         dt.accent),
            "warning": (rgba(dt.warning, 0.12),        rgba(dt.warning, 0.35),        dt.warning),
            "danger":  (rgba(dt.danger, 0.12),         rgba(dt.danger, 0.35),         dt.danger),
            "success": (rgba(dt.success_bright, 0.12), rgba(dt.success_bright, 0.35), dt.success_bright),
            "preview": (rgba(dt.text_muted, 0.1),      rgba(dt.text_muted, 0.25),     dt.text_muted),
        }
        background, border, accent = mapping.get(self._tone, mapping["neutral"])
        self.setStyleSheet(
            f"""
            QFrame#infoBanner {{
                background-color: {background};
                border: 1px solid {border};
                border-radius: 12px;
            }}
            """
        )
        self.title_label.setStyleSheet(f"color: {accent};")
        self.message_label.setStyleSheet(f"color: {dt.text_secondary}; font-size: 12px;")


class EmptyState(QFrame, ThemedWidget):
    def __init__(self, title: str, message: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("emptyState")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(6)

        self.title_label = QLabel(title)
        title_font = QFont("Segoe UI", 11)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        layout.addWidget(self.title_label)

        self.message_label = QLabel(message)
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)

        layout.addStretch()
        self.refresh_theme()

    def refresh_theme(self) -> None:
        dt = self.dt
        self.setStyleSheet(
            f"""
            QFrame#emptyState {{
                background-color: {rgba(dt.surface, 0.42)};
                border: 1px solid {rgba(dt.border_strong, 0.72)};
                border-radius: 12px;
            }}
            """
        )
        self.title_label.setStyleSheet(f"color: {dt.text_primary};")
        self.message_label.setStyleSheet(f"color: {dt.text_secondary}; font-size: 12px;")


class ActionTileButton(QPushButton, ThemedWidget):
    def __init__(
        self,
        title: str,
        note: str,
        variant: str = "secondary",
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._variant = variant
        self._note = note
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(76)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        self.title_label = QLabel(title)
        title_font = QFont("Segoe UI", 10)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        layout.addWidget(self.title_label)

        self.note_label = QLabel(note)
        self.note_label.setWordWrap(True)
        layout.addWidget(self.note_label)

        self.refresh_theme()

    def set_note(self, note: str) -> None:
        self._note = note
        self.note_label.setText(note)

    def refresh_theme(self) -> None:
        dt = self.dt
        variants = {
            "secondary": (dt.surface,              rgba(dt.border_strong, 0.9),  dt.text_primary, dt.text_secondary),
            "danger":    (rgba(dt.danger, 0.08),   rgba(dt.danger, 0.35),        dt.text_primary, dt.text_secondary),
            "preview":   (rgba(dt.text_muted, 0.1), rgba(dt.text_muted, 0.22),   dt.text_muted,   dt.text_muted),
        }
        background, border, title, note = variants.get(self._variant, variants["secondary"])
        self.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {background};
                border: 1px solid {border};
                border-radius: 12px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {rgba(dt.surface_raised, 0.6)};
            }}
            QPushButton:disabled {{
                background-color: {background};
                border-color: {border};
            }}
            """
        )
        self.title_label.setStyleSheet(f"color: {title};")
        self.note_label.setStyleSheet(f"color: {note}; font-size: 12px;")


class SidebarStatusPanel(QFrame, ThemedWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("sidebarStatusPanel")
        self._muted_labels: list[QLabel] = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        self.status_chip = StatusChip("Disconnected", "danger")
        layout.addWidget(self.status_chip, 0, Qt.AlignmentFlag.AlignLeft)

        self.status_message = QLabel("Not connected")
        self.status_message.setWordWrap(True)
        layout.addWidget(self.status_message)

        self.user_value = QLabel("Not connected")
        self.guilds_value = QLabel("0")
        self.ping_value = QLabel("-- ms")

        for label, value in (
            ("User", self.user_value),
            ("Guilds", self.guilds_value),
            ("Ping", self.ping_value),
        ):
            row = QHBoxLayout()
            row.setSpacing(8)
            key = QLabel(label)
            key.setProperty("role", "muted")
            self._muted_labels.append(key)
            row.addWidget(key)
            row.addStretch()
            row.addWidget(value)
            layout.addLayout(row)

        layout.addStretch()
        self.refresh_theme()

    def set_connection_state(self, connected: bool, username: str = "", message: str = "") -> None:
        if connected:
            self.status_chip.setText("Connected")
            self.status_chip.set_tone("success")
            self.user_value.setText(username or "Connected")
            self.status_message.setText(message or "Bot session is active.")
        else:
            self.status_chip.setText("Disconnected")
            self.status_chip.set_tone("danger")
            self.user_value.setText("Not connected")
            self.guilds_value.setText("0")
            self.ping_value.setText("-- ms")
            self.status_message.setText(message or "Enter a token on the Login page to connect.")

    def set_status_message(self, message: str, tone: str = "neutral") -> None:
        self.status_message.setText(message)
        self.status_chip.set_tone(tone)

    def set_guild_count(self, count: int) -> None:
        self.guilds_value.setText(str(count))

    def set_ping(self, ping_ms: Optional[float]) -> None:
        if ping_ms is None:
            self.ping_value.setText("-- ms")
            return
        self.ping_value.setText(f"{ping_ms:.0f} ms")

    def refresh_theme(self) -> None:
        dt = self.dt
        self.setStyleSheet(
            f"""
            QFrame#sidebarStatusPanel {{
                background-color: {rgba(dt.surface, 0.32)};
                border: 1px solid {rgba(dt.border_strong, 0.82)};
                border-radius: 14px;
            }}
            """
        )
        self.status_message.setStyleSheet(f"color: {dt.text_secondary}; font-size: 12px;")
        self.user_value.setStyleSheet(f"color: {dt.text_primary};")
        self.guilds_value.setStyleSheet(f"color: {dt.text_primary};")
        self.ping_value.setStyleSheet(f"color: {dt.text_primary};")
        for label in self._muted_labels:
            label.setStyleSheet(
                f"color: {dt.text_muted}; font-size: 10px; font-weight: 700; letter-spacing: 0.8px;"
            )
        self.status_chip.refresh_theme()


def apply_theme_to_widgets(widgets: Iterable[QWidget]) -> None:
    for widget in widgets:
        refresh = getattr(widget, "refresh_theme", None)
        if callable(refresh):
            refresh()
