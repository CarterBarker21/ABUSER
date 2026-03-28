"""Guild overview page - displays server statistics in a clean table view."""

from __future__ import annotations

from typing import Dict, List, Optional
from datetime import datetime

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QBrush, QColor, QPainterPath
from PyQt6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QFrame,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..components import (
    AppButton,
    EmptyState,
    InfoBanner,
    PanelCard,
    SearchField,
    SectionLabel,
    StatusChip,
    rgba,
)
from ..theme import get_theme_manager
from .base import BasePage, GuildItem


class GuildStatCard(QWidget):
    """A wide card displaying a single guild's statistics in 2 lines."""

    # Discord permission bitflags
    PERM_KICK_MEMBERS = 1 << 1
    PERM_BAN_MEMBERS = 1 << 2
    PERM_MANAGE_CHANNELS = 1 << 4

    def __init__(self, guild: GuildItem, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.guild = guild
        self.setObjectName("guildStatCard")
        self.theme_manager = get_theme_manager()
        self._build_ui()
        self.refresh_theme()

    # Fixed purple color for Owner status (consistent regardless of theme accent)
    OWNER_COLOR = "#9B59B6"  # Purple
    
    def _get_status_info(self) -> tuple[str, str, str]:
        """Determine status color and tooltip based on permissions.
        
        Returns:
            Tuple of (color_hex, status_text, tooltip)
        """
        colors = self.theme_manager.theme
        
        # Debug: Check is_owner status
        print(f"[DEBUG _get_status_info] Guild: {self.guild.name}, is_owner={self.guild.is_owner}, type={type(self.guild.is_owner)}")
        
        if self.guild.is_owner:
            print(f"[DEBUG] -> Owner status detected for {self.guild.name}")
            return (self.OWNER_COLOR, "Owner", "You own this server (full control)")
        
        perms = self.guild.my_permissions
        has_ban = bool(perms & self.PERM_BAN_MEMBERS)
        has_manage_channels = bool(perms & self.PERM_MANAGE_CHANNELS)
        has_kick = bool(perms & self.PERM_KICK_MEMBERS)
        
        if has_ban and has_manage_channels:
            return (colors.success_bright, "Full Perms", "Has ban + manage_channels permissions")
        elif has_kick:
            return (colors.warning, "Kick Only", "Has kick permission but not ban")
        else:
            return (colors.error, "No Perms", "No significant permissions")

    # Icon size for guild avatars
    ICON_SIZE = 44
    
    # Discord-like colors for placeholder icons
    PLACEHOLDER_COLORS = [
        "#5865F2",  # Discord Blurple
        "#EB459E",  # Pink
        "#3BA55D",  # Green
        "#FAA81A",  # Yellow
        "#ED4245",  # Red
        "#57F287",  # Light Green
        "#9B59B6",  # Purple
        "#1ABC9C",  # Teal
    ]
    
    def _get_placeholder_color(self) -> str:
        """Get a consistent color for this guild based on its name."""
        # Use sum of character codes for consistent color selection
        name_hash = sum(ord(c) for c in self.guild.name) if self.guild.name else 0
        return self.PLACEHOLDER_COLORS[name_hash % len(self.PLACEHOLDER_COLORS)]
    
    def _create_circular_pixmap(self, source: QPixmap) -> QPixmap:
        """Create a circular clipped pixmap from a source pixmap."""
        # Scale to fit
        scaled = source.scaled(
            self.ICON_SIZE, self.ICON_SIZE, 
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )
        
        # Center crop if needed
        if scaled.width() > self.ICON_SIZE or scaled.height() > self.ICON_SIZE:
            x = (scaled.width() - self.ICON_SIZE) // 2
            y = (scaled.height() - self.ICON_SIZE) // 2
            scaled = scaled.copy(x, y, self.ICON_SIZE, self.ICON_SIZE)
        
        # Create target with transparency
        target = QPixmap(self.ICON_SIZE, self.ICON_SIZE)
        target.fill(Qt.GlobalColor.transparent)
        
        # Paint circular clip
        painter = QPainter(target)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # Create circular mask
        path = QPainterPath()
        path.addEllipse(0, 0, self.ICON_SIZE, self.ICON_SIZE)
        painter.setClipPath(path)
        
        # Draw image
        painter.drawPixmap(0, 0, scaled)
        painter.end()
        
        return target
    
    def _create_placeholder_pixmap(self) -> QPixmap:
        """Create a placeholder icon with the guild's first letter."""
        pixmap = QPixmap(self.ICON_SIZE, self.ICON_SIZE)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get consistent color for this guild
        bg_color = QColor(self._get_placeholder_color())
        
        # Draw circle background
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, self.ICON_SIZE, self.ICON_SIZE)
        
        # Draw first letter
        painter.setPen(Qt.GlobalColor.white)
        font = painter.font()
        font.setPointSize(16)
        font.setBold(True)
        painter.setFont(font)
        
        first_letter = self.guild.name[0].upper() if self.guild.name else "?"
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, first_letter)
        painter.end()
        
        return pixmap
    
    def _create_icon_label(self) -> QLabel:
        """Create the guild icon label with real icon or placeholder."""
        icon_label = QLabel()
        icon_label.setFixedSize(self.ICON_SIZE, self.ICON_SIZE)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Try to use real icon data first
        if self.guild.icon_data:
            try:
                pixmap = QPixmap()
                if pixmap.loadFromData(self.guild.icon_data):
                    circular = self._create_circular_pixmap(pixmap)
                    icon_label.setPixmap(circular)
                    return icon_label
            except Exception:
                pass  # Fall through to placeholder
        
        # Use placeholder
        icon_label.setPixmap(self._create_placeholder_pixmap())
        return icon_label
    
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # Line 1: Icon + Server Name + ID (left-aligned) + Status Circle (right)
        line1_layout = QHBoxLayout()
        line1_layout.setSpacing(12)
        
        # Guild Icon (leftmost)
        self.icon_label = self._create_icon_label()
        line1_layout.addWidget(self.icon_label, 0, Qt.AlignmentFlag.AlignVCenter)

        # Name and ID container (middle)
        name_container = QHBoxLayout()
        name_container.setSpacing(8)
        
        self.name_label = QLabel(self.guild.name)
        self.name_label.setWordWrap(False)
        name_container.addWidget(self.name_label)

        self.id_label = QLabel(f"({self.guild.id})")
        name_container.addWidget(self.id_label)
        name_container.addStretch(1)
        
        line1_layout.addLayout(name_container, 1)

        # Status indicator (right side)
        color_hex, status_text, tooltip = self._get_status_info()
        self.status_circle = QLabel()
        self.status_circle.setFixedSize(14, 14)
        self.status_circle.setStyleSheet(f"""
            QLabel {{
                background-color: {color_hex};
                border-radius: 7px;
                border: 2px solid {color_hex};
            }}
        """)
        self.status_circle.setToolTip(tooltip)
        line1_layout.addWidget(self.status_circle, 0, Qt.AlignmentFlag.AlignVCenter)

        layout.addLayout(line1_layout)

        # Line 2: Stats row (Members | Channels | Roles | Boosts | Created)
        line2_layout = QHBoxLayout()
        line2_layout.setSpacing(24)

        # Members
        members_layout = QHBoxLayout()
        members_layout.setSpacing(4)
        self.members_label = QLabel("Members:")
        self.members_value = QLabel(f"{self.guild.member_count:,}")
        members_layout.addWidget(self.members_label)
        members_layout.addWidget(self.members_value)
        line2_layout.addLayout(members_layout)

        # Channels
        channels_layout = QHBoxLayout()
        channels_layout.setSpacing(4)
        self.channels_label = QLabel("Channels:")
        self.channels_value = QLabel(str(self.guild.channels_count))
        channels_layout.addWidget(self.channels_label)
        channels_layout.addWidget(self.channels_value)
        line2_layout.addLayout(channels_layout)

        # Roles
        roles_layout = QHBoxLayout()
        roles_layout.setSpacing(4)
        self.roles_label = QLabel("Roles:")
        self.roles_value = QLabel(str(self.guild.roles_count))
        roles_layout.addWidget(self.roles_label)
        roles_layout.addWidget(self.roles_value)
        line2_layout.addLayout(roles_layout)

        # Boosts
        boosts_layout = QHBoxLayout()
        boosts_layout.setSpacing(4)
        self.boosts_label = QLabel("Boosts:")
        self.boosts_value = QLabel(str(getattr(self.guild, 'boost_count', 0) or 0))
        boosts_layout.addWidget(self.boosts_label)
        boosts_layout.addWidget(self.boosts_value)
        line2_layout.addLayout(boosts_layout)

        # Created
        created_layout = QHBoxLayout()
        created_layout.setSpacing(4)
        self.created_label = QLabel("Created:")
        self.created_value = QLabel(
            self.guild.created_at.strftime("%Y-%m-%d") if self.guild.created_at else "Unknown"
        )
        created_layout.addWidget(self.created_label)
        created_layout.addWidget(self.created_value)
        line2_layout.addLayout(created_layout)

        line2_layout.addStretch(1)
        layout.addLayout(line2_layout)

    def refresh_theme(self) -> None:
        colors = self.theme_manager.theme

        # Update status circle with current theme colors
        color_hex, status_text, tooltip = self._get_status_info()
        self.status_circle.setStyleSheet(f"""
            QLabel {{
                background-color: {color_hex};
                border-radius: 7px;
                border: 2px solid {color_hex};
            }}
        """)

        # Card styling - wider card with subtle border
        self.setStyleSheet(
            f"""
            QWidget#guildStatCard {{
                background-color: {colors.card_bg};
                border: 1px solid {rgba(colors.border_light, 0.9)};
                border-radius: 12px;
            }}
            """
        )

        # Name styling (large, bold, primary color)
        self.name_label.setStyleSheet(
            f"color: {colors.text_primary}; font-size: 16px; font-weight: 700;"
        )

        # ID styling (muted, monospace)
        self.id_label.setStyleSheet(
            f"color: {colors.text_muted}; font-size: 12px; font-family: monospace;"
        )

        # Label styling (muted)
        label_style = f"color: {colors.text_muted}; font-size: 12px; font-weight: 500;"
        self.members_label.setStyleSheet(label_style)
        self.channels_label.setStyleSheet(label_style)
        self.roles_label.setStyleSheet(label_style)
        self.boosts_label.setStyleSheet(label_style)
        self.created_label.setStyleSheet(label_style)

        # Value styling (accent for members, secondary for others)
        self.members_value.setStyleSheet(
            f"color: {colors.accent_primary}; font-size: 13px; font-weight: 700;"
        )
        value_style = f"color: {colors.text_secondary}; font-size: 13px; font-weight: 600;"
        self.channels_value.setStyleSheet(value_style)
        self.roles_value.setStyleSheet(value_style)
        self.boosts_value.setStyleSheet(value_style)
        self.created_value.setStyleSheet(value_style)


class GuildsPage(BasePage):
    """Overview page displaying all connected servers in a clean grid layout."""

    refresh_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(
            "Guilds",
            eyebrow="Servers",
            parent=parent,
        )
        # Remove header to keep it clean - just card and search
        self.root_layout.removeWidget(self.header)
        self.header.hide()
        
        self._guilds: Dict[int, GuildItem] = {}
        self._connected = False
        self._guild_cards: List[GuildStatCard] = []
        self._build_ui()

    def _build_ui(self) -> None:
        # Full width layout - use maximum available space
        scroll, body_layout = self._create_full_width_body()
        self.root_layout.addWidget(scroll, 1)

        # Toolbar with search and refresh
        toolbar = QHBoxLayout()
        toolbar.setSpacing(self.tokens.metrics.spacing_md)

        self.search_input = SearchField("Search servers...")
        self.search_input.textChanged.connect(self._filter_guilds)
        toolbar.addWidget(self.search_input, 1)

        self.connection_chip = StatusChip("Disconnected", "danger")
        toolbar.addWidget(self.connection_chip)

        self.refresh_button = AppButton("Refresh", "secondary")
        self.refresh_button.clicked.connect(self.refresh_requested.emit)
        toolbar.addWidget(self.refresh_button)

        body_layout.addLayout(toolbar)

        # Main panel card with custom header for legend
        self.overview_card = QWidget()
        self.overview_card.setObjectName("overviewCard")
        card_layout = QVBoxLayout(self.overview_card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(14)
        
        # Custom header with title and legend
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)
        
        # Title
        self.overview_title = QLabel("Server Overview")
        title_font = self.font()
        title_font.setPointSize(12)
        title_font.setBold(True)
        self.overview_title.setFont(title_font)
        header_layout.addWidget(self.overview_title)
        
        header_layout.addStretch(1)
        
        # Legend
        legend_widget = QWidget()
        legend_layout = QHBoxLayout(legend_widget)
        legend_layout.setContentsMargins(0, 0, 0, 0)
        legend_layout.setSpacing(16)
        
        # Legend items: No Perms, Kick Only, Full Perms, Owner
        legend_items = [
            ("🔴", "No Perms", "danger"),
            ("🟡", "Kick Only", "warning"),
            ("🟢", "Full Perms", "success"),
            ("🟣", "Owner", "accent"),
        ]
        
        for emoji, text, tone in legend_items:
            item = QLabel(f"{emoji} {text}")
            item.setStyleSheet(f"color: {self.theme.text_secondary}; font-size: 11px;")
            legend_layout.addWidget(item)
        
        header_layout.addWidget(legend_widget)
        card_layout.addWidget(header_widget)
        
        # Body layout for guilds
        self.overview_body = QVBoxLayout()
        self.overview_body.setContentsMargins(0, 0, 0, 0)
        self.overview_body.setSpacing(14)
        card_layout.addLayout(self.overview_body)
        
        self.overview_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        body_layout.addWidget(self.overview_card, 1)

        # Empty state
        self.empty_state = EmptyState(
            "No guilds available",
            "Connect to Discord to view your server statistics.",
        )
        self.overview_body.addWidget(self.empty_state)

        # Guilds vertical stack container (single column, wider cards)
        self.guilds_container = QWidget()
        self.guilds_layout = QVBoxLayout(self.guilds_container)
        self.guilds_layout.setContentsMargins(0, 0, 0, 0)
        self.guilds_layout.setSpacing(8)  # Tighter spacing between cards
        self.guilds_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.overview_body.addWidget(self.guilds_container)
        self.guilds_container.hide()

        # Status banner at bottom
        self.status_banner = InfoBanner(
            "Disconnected",
            "Connect on the Login page to populate the server overview.",
            tone="neutral",
        )
        body_layout.addWidget(self.status_banner)

        body_layout.addStretch(0)
        self.refresh_theme()

    def _create_centered_body(self, max_width: int = 960) -> tuple[QScrollArea, QVBoxLayout]:
        """Create a centered scroll body matching Login tab style."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        wrapper = QWidget()
        wrapper_layout = QHBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.setSpacing(0)

        wrapper_layout.addStretch(1)

        body = QWidget()
        body.setMaximumWidth(max_width)
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(self.tokens.metrics.spacing_lg)

        wrapper_layout.addWidget(body)
        wrapper_layout.addStretch(1)

        scroll.setWidget(wrapper)
        return scroll, body_layout

    def _create_full_width_body(self) -> tuple[QScrollArea, QVBoxLayout]:
        """Create a full-width scroll body that fills available space."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(24, 24, 24, 24)  # Add some padding
        body_layout.setSpacing(self.tokens.metrics.spacing_lg)

        scroll.setWidget(body)
        return scroll, body_layout

    def set_connected(self, connected: bool, user_name: str = "") -> None:
        """Update connection state and UI."""
        self._connected = connected
        if connected:
            self.connection_chip.setText("Connected")
            self.connection_chip.set_tone("success")
            self.status_banner.title_label.setText("Connected")
            self.status_banner.message_label.setText(
                f"Server data is live for {user_name or 'the active session'}. Use Refresh to update."
            )
            self.status_banner._tone = "success"
        else:
            self.connection_chip.setText("Disconnected")
            self.connection_chip.set_tone("danger")
            self.status_banner.title_label.setText("Disconnected")
            self.status_banner.message_label.setText("Connect on the Login page to view server statistics.")
            self.status_banner._tone = "neutral"
            self.update_guilds([])
        self.status_banner.refresh_theme()

    def update_guilds(self, guilds: List[GuildItem]) -> None:
        """Update the guilds display with new data."""
        # Debug: Check for owned servers
        owned_servers = [g.name for g in guilds if g.is_owner]
        if owned_servers:
            print(f"[GUILDS DEBUG] Owned servers in update_guilds: {owned_servers}")
        
        # Clear existing cards
        self._clear_guild_cards()
        self._guilds = {guild.id: guild for guild in guilds}

        # Sort by member count (highest first), then by name
        sorted_guilds = sorted(
            guilds,
            key=lambda g: (-g.member_count, g.name.lower())
        )

        if not sorted_guilds:
            self.empty_state.show()
            self.guilds_container.hide()
            self.status_banner.title_label.setText("No servers")
            self.status_banner.message_label.setText("No guilds found for this account.")
        else:
            self.empty_state.hide()
            self.guilds_container.show()
            self._create_guild_cards(sorted_guilds)
            self.status_banner.title_label.setText(f"{len(sorted_guilds)} servers loaded")
            self.status_banner.message_label.setText(
                f"Total members across all servers: {sum(g.member_count for g in sorted_guilds):,}"
            )

        self.status_banner.refresh_theme()

    def _clear_guild_cards(self) -> None:
        """Remove all guild cards and section headers from the layout."""
        for card in self._guild_cards:
            card.deleteLater()
        self._guild_cards.clear()

        # Clear the vertical layout completely
        while self.guilds_layout.count():
            item = self.guilds_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

    def _create_section_header(self, title: str, color_hex: str) -> QWidget:
        """Create a section header with a colored indicator and title."""
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 8, 0, 8)
        header_layout.setSpacing(12)
        
        # Colored indicator dot
        indicator = QLabel()
        indicator.setFixedSize(10, 10)
        indicator.setStyleSheet(f"""
            QLabel {{
                background-color: {color_hex};
                border-radius: 5px;
            }}
        """)
        header_layout.addWidget(indicator)
        
        # Section title
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.text_primary};
                font-size: 13px;
                font-weight: 700;
            }}
        """)
        header_layout.addWidget(title_label)
        
        # Horizontal line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background-color: {self.theme.divider};")
        line.setFixedHeight(1)
        header_layout.addWidget(line, 1)
        
        return header
    
    def _create_divider(self) -> QFrame:
        """Create a clean horizontal divider line between guild cards."""
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme.divider};
                border: none;
            }}
        """)
        line.setFixedHeight(1)
        return line
    
    def _get_guild_status_key(self, guild: GuildItem) -> int:
        """Get sort key for grouping guilds by status.
        
        Returns:
            0 = Owner (highest priority)
            1 = Full Perms
            2 = Kick Only
            3 = No Perms (lowest priority)
        """
        if guild.is_owner:
            return 0
        perms = guild.my_permissions
        has_ban = bool(perms & GuildStatCard.PERM_BAN_MEMBERS)
        has_manage = bool(perms & GuildStatCard.PERM_MANAGE_CHANNELS)
        has_kick = bool(perms & GuildStatCard.PERM_KICK_MEMBERS)
        
        if has_ban and has_manage:
            return 1
        elif has_kick:
            return 2
        else:
            return 3
    
    def _create_guild_cards(self, guilds: List[GuildItem]) -> None:
        """Create and layout guild stat cards with section dividers and card dividers.
        
        Groups guilds by permission level with section headers and adds
        clean dividers between each guild card.
        """
        # Sort by status priority, then by member count
        sorted_guilds = sorted(guilds, key=lambda g: (self._get_guild_status_key(g), -g.member_count))
        
        # Group by status
        current_section = None
        section_info = {
            0: ("Owned Servers", GuildStatCard.OWNER_COLOR),
            1: ("Full Permissions", None),  # Use theme success color later
            2: ("Kick Only", None),  # Use theme warning color later
            3: ("No Permissions", None),  # Use theme error color later
        }
        
        previous_card = None  # Track previous card to add dividers between guilds
        
        for i, guild in enumerate(sorted_guilds):
            status_key = self._get_guild_status_key(guild)
            
            # Add section header when status changes
            if status_key != current_section:
                current_section = status_key
                section_name, section_color = section_info[status_key]
                
                # Get color from theme for non-owner sections
                if section_color is None:
                    if status_key == 1:
                        section_color = self.theme.success_bright
                    elif status_key == 2:
                        section_color = self.theme.warning
                    else:
                        section_color = self.theme.error
                
                header = self._create_section_header(section_name, section_color)
                self.guilds_layout.addWidget(header)
                self._guild_cards.append(header)  # Track for cleanup
                previous_card = None  # Reset - no divider after section header
            
            # Add divider between guilds (but not before the first one or after section header)
            if previous_card is not None:
                divider = self._create_divider()
                self.guilds_layout.addWidget(divider)
                self._guild_cards.append(divider)  # Track for cleanup
            
            card = GuildStatCard(guild)
            self.guilds_layout.addWidget(card)
            self._guild_cards.append(card)
            previous_card = card

    def add_guild(self, guild: GuildItem) -> None:
        """Add a single guild to the display."""
        guilds = list(self._guilds.values())
        guilds.append(guild)
        self.update_guilds(guilds)

    def remove_guild(self, guild_id: int) -> None:
        """Remove a guild from the display."""
        guilds = [guild for gid, guild in self._guilds.items() if gid != guild_id]
        self.update_guilds(guilds)

    def _filter_guilds(self, text: str) -> None:
        """Filter displayed guilds based on search text.
        
        Hides section headers when all guilds in that section are filtered out.
        Hides dividers when adjacent guilds are filtered out.
        """
        text = text.lower().strip()
        visible_count = 0
        section_has_visible = False
        current_section_header = None
        
        # First pass: determine visibility for all cards
        card_visibility = []  # List of (widget, is_guild_card, should_be_visible)
        
        for card in self._guild_cards:
            if isinstance(card, GuildStatCard):
                # Guild card - check if it matches filter
                match = text in card.guild.name.lower() or text in str(card.guild.id)
                card_visibility.append((card, True, match))
                if match:
                    visible_count += 1
                    section_has_visible = True
            elif isinstance(card, QFrame):
                # Divider line - we'll determine visibility in second pass
                card_visibility.append((card, False, False))  # Placeholder
            else:
                # Section header - show/hide based on previous section's visibility
                if current_section_header is not None:
                    card_visibility.append((current_section_header, False, section_has_visible))
                current_section_header = card
                section_has_visible = False
        
        # Handle last section header
        if current_section_header is not None:
            card_visibility.append((current_section_header, False, section_has_visible))
        
        # Second pass: determine divider visibility based on adjacent guilds
        for i, (widget, is_guild, visible) in enumerate(card_visibility):
            if isinstance(widget, QFrame) and not is_guild:
                # This is a divider - show only if guild before AND after are visible
                guild_before_visible = False
                guild_after_visible = False
                
                # Look for visible guild before this divider
                for j in range(i - 1, -1, -1):
                    if card_visibility[j][1]:  # Is guild card
                        guild_before_visible = card_visibility[j][2]
                        break
                
                # Look for visible guild after this divider
                for j in range(i + 1, len(card_visibility)):
                    if card_visibility[j][1]:  # Is guild card
                        guild_after_visible = card_visibility[j][2]
                        break
                
                # Divider visible only if both adjacent guilds are visible
                card_visibility[i] = (widget, is_guild, guild_before_visible and guild_after_visible)
        
        # Apply visibility
        for widget, is_guild, should_show in card_visibility:
            widget.setVisible(should_show)

        # Show/hide empty state based on filter results
        if self._guild_cards and visible_count == 0:
            self.empty_state.show()
            self.empty_state.title_label.setText("No search results")
            self.empty_state.message_label.setText("Try a different server name or clear the search field.")
            self.guilds_container.hide()
        else:
            self.empty_state.hide()
            self.guilds_container.show()

    def refresh_theme(self) -> None:
        """Refresh the theme for all components."""
        super().refresh_theme()

        colors = self.theme

        # Refresh overview card styling
        self.overview_card.setStyleSheet(
            f"""
            QWidget#overviewCard {{
                background-color: {colors.card_bg};
                border: 1px solid {rgba(colors.border_light, 0.9)};
                border-radius: {self.tokens.metrics.card_radius}px;
            }}
            """
        )
        self.overview_title.setStyleSheet(f"color: {colors.text_primary};")
        
        # Refresh legend colors
        legend_widget = self.overview_card.findChild(QWidget, "")
        if legend_widget:
            for child in legend_widget.findChildren(QLabel):
                if "No Perms" in child.text() or "Kick Only" in child.text() or "Full Perms" in child.text() or "Owner" in child.text():
                    child.setStyleSheet(f"color: {colors.text_secondary}; font-size: 11px;")

        # Refresh status banner
        self.status_banner.refresh_theme()

        # Refresh connection chip
        self.connection_chip.refresh_theme()

        # Refresh empty state
        self.empty_state.refresh_theme()

        # Refresh all guild cards and section headers
        for card in self._guild_cards:
            if isinstance(card, GuildStatCard):
                card.refresh_theme()
            # Section headers don't need theme refresh - they're static

        # Refresh buttons
        self.refresh_button.refresh_theme()
        self.search_input.refresh_theme()
