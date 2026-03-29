"""DM page with an honest local-only queue."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ..components import (
    ActionTileButton,
    AppButton,
    AppComboBox,
    AppLineEdit,
    AppSpinBox,
    AppTextEdit,
    EmptyState,
    InfoBanner,
    PanelCard,
    SectionLabel,
    rgba,
)
from ..theme import get_theme_manager
from .base import BasePage


class DMPage(BasePage):
    dm_action_requested = pyqtSignal(str, dict)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(
            "Direct Messages",
            "Compose drafts, manage a local queue, and keep unsupported delivery tools clearly marked as unavailable.",
            eyebrow="Queue",
            parent=parent,
        )
        self.root_layout.removeWidget(self.header)
        self.header.hide()

        self._queue: list[dict[str, str | int]] = []
        self._build_ui()

    def _build_ui(self) -> None:
        # Full-width scroll area, matching Guilds/Nuker pattern
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(24, 24, 24, 24)
        body_layout.setSpacing(16)
        scroll.setWidget(body)
        self.root_layout.addWidget(scroll, 1)

        # ── Availability banner ───────────────────────────────────────────────
        body_layout.addWidget(
            InfoBanner(
                "Delivery unavailable",
                "This build keeps the DM composer and queue visible, but message delivery "
                "and bulk tools remain disabled.",
                tone="preview",
            )
        )

        # ── Composer card ─────────────────────────────────────────────────────
        compose_card = PanelCard("Message Composer", "Build a draft and stage it in the local queue.")
        body_layout.addWidget(compose_card)

        # Recipient + template row
        fields_row = QHBoxLayout()
        fields_row.setSpacing(16)

        recipient_col = QVBoxLayout()
        recipient_col.setSpacing(6)
        recipient_col.addWidget(SectionLabel("Recipient"))
        self.recipient_input = AppLineEdit("User ID or @username")
        recipient_col.addWidget(self.recipient_input)
        fields_row.addLayout(recipient_col, 1)

        template_col = QVBoxLayout()
        template_col.setSpacing(6)
        template_col.addWidget(SectionLabel("Template"))
        self.template_combo = AppComboBox()
        self.template_combo.addItems(["Custom Message", "Short Greeting", "Follow-up Note"])
        template_col.addWidget(self.template_combo)
        fields_row.addLayout(template_col, 1)

        compose_card.body_layout.addLayout(fields_row)

        # Message body
        compose_card.body_layout.addWidget(SectionLabel("Message"))
        self.message_input = AppTextEdit("Type your draft here")
        self.message_input.setMinimumHeight(160)
        self.message_input.textChanged.connect(self._update_character_count)
        compose_card.body_layout.addWidget(self.message_input)

        # Count / delay / char count row
        meta_row = QHBoxLayout()
        meta_row.setSpacing(16)

        count_col = QVBoxLayout()
        count_col.setSpacing(4)
        count_col.addWidget(SectionLabel("Count"))
        self.count_spin = AppSpinBox()
        self.count_spin.setRange(1, 50)
        self.count_spin.setValue(1)
        count_col.addWidget(self.count_spin)
        meta_row.addLayout(count_col)

        delay_col = QVBoxLayout()
        delay_col.setSpacing(4)
        delay_col.addWidget(SectionLabel("Delay (ms)"))
        self.delay_spin = AppSpinBox()
        self.delay_spin.setRange(250, 30000)
        self.delay_spin.setSingleStep(250)
        self.delay_spin.setValue(1000)
        delay_col.addWidget(self.delay_spin)
        meta_row.addLayout(delay_col)

        meta_row.addStretch(1)
        self.character_count = QLabel("0 / 2000")
        self.character_count.setObjectName("charCount")
        meta_row.addWidget(self.character_count)
        compose_card.body_layout.addLayout(meta_row)

        # Action buttons
        action_row = QHBoxLayout()
        action_row.setSpacing(12)
        self.queue_button = AppButton("Add to Queue", "secondary")
        self.queue_button.clicked.connect(self._add_to_queue)
        action_row.addWidget(self.queue_button)
        self.send_button = AppButton("Send — Unavailable", "preview")
        self.send_button.setEnabled(False)
        action_row.addWidget(self.send_button)
        action_row.addStretch(1)
        compose_card.body_layout.addLayout(action_row)

        # ── Queue card ────────────────────────────────────────────────────────
        queue_card = PanelCard("Send Queue", "Review locally staged drafts and clear them when needed.")
        body_layout.addWidget(queue_card)

        self.queue_stack = QStackedWidget()
        self.queue_empty = EmptyState(
            "Queue is empty",
            "Drafts added from the composer will appear here for local review.",
        )
        self.queue_stack.addWidget(self.queue_empty)
        self.queue_list = QListWidget()
        self.queue_stack.addWidget(self.queue_list)
        queue_card.body_layout.addWidget(self.queue_stack)

        queue_controls = QHBoxLayout()
        queue_controls.setSpacing(12)
        self.queue_count_label = QLabel("0 queued")
        self.queue_count_label.setObjectName("queueCount")
        queue_controls.addWidget(self.queue_count_label)
        queue_controls.addStretch(1)
        clear_button = AppButton("Clear Queue", "tertiary")
        clear_button.clicked.connect(self._clear_queue)
        queue_controls.addWidget(clear_button)
        queue_card.body_layout.addLayout(queue_controls)

        # ── Secondary tools card ──────────────────────────────────────────────
        tools_card = PanelCard(
            "Secondary Tools",
            "Visible for interface completeness — marked unavailable in this build.",
        )
        body_layout.addWidget(tools_card)

        # 2-column grid of tiles
        tools_grid = QHBoxLayout()
        tools_grid.setSpacing(12)

        left_col = QVBoxLayout()
        left_col.setSpacing(8)
        right_col = QVBoxLayout()
        right_col.setSpacing(8)

        tool_labels = [
            "Mass DM Friends",
            "Mass DM Guild",
            "DM Advertise",
            "Close All DMs",
            "Clear DMs",
            "DM Spammer",
        ]
        for i, label in enumerate(tool_labels):
            tile = ActionTileButton(label, "Unavailable in this build.", variant="preview")
            tile.setEnabled(False)
            (left_col if i % 2 == 0 else right_col).addWidget(tile)

        tools_grid.addLayout(left_col, 1)
        tools_grid.addLayout(right_col, 1)
        tools_card.body_layout.addLayout(tools_grid)

        body_layout.addStretch(1)
        self.refresh_theme()
        self._update_queue_view()

    # ── Logic ─────────────────────────────────────────────────────────────────

    def _update_character_count(self) -> None:
        count = len(self.message_input.toPlainText())
        self.character_count.setText(f"{count} / 2000")

    def _add_to_queue(self) -> None:
        recipient = self.recipient_input.text().strip()
        message = self.message_input.toPlainText().strip()
        if not recipient or not message:
            return
        self._queue.append(
            {
                "recipient": recipient,
                "message": message,
                "count": self.count_spin.value(),
                "delay": self.delay_spin.value(),
            }
        )
        self._update_queue_view()

    def _clear_queue(self) -> None:
        self._queue.clear()
        self._update_queue_view()

    def _update_queue_view(self) -> None:
        self.queue_list.clear()
        for draft in self._queue:
            preview = draft["message"][:60]
            if len(str(draft["message"])) > 60:
                preview += "…"
            item = QListWidgetItem(
                f"{draft['recipient']}  |  {draft['count']}x @ {draft['delay']} ms\n{preview}"
            )
            self.queue_list.addItem(item)
        has_items = bool(self._queue)
        self.queue_stack.setCurrentWidget(self.queue_list if has_items else self.queue_empty)
        self.queue_count_label.setText(f"{len(self._queue)} queued")

    # ── Theme ─────────────────────────────────────────────────────────────────

    def refresh_theme(self) -> None:
        super().refresh_theme()
        dt = get_theme_manager().design_tokens
        self.queue_list.setStyleSheet(
            f"""
            QListWidget {{
                background-color: {dt.surface_raised};
                color: {dt.text_primary};
                border: 1px solid {rgba(dt.border_strong, 0.9)};
                border-radius: 10px;
                padding: 6px;
            }}
            QListWidget::item {{
                padding: 10px 12px;
                border-radius: 6px;
                border-bottom: 1px solid {rgba(dt.border_strong, 0.5)};
            }}
            QListWidget::item:selected {{
                background-color: {rgba(dt.accent, 0.2)};
                color: {dt.text_primary};
            }}
            """
        )
        self.queue_count_label.setStyleSheet(
            f"color: {dt.text_secondary}; background: transparent;"
        )
        self.character_count.setStyleSheet(
            f"color: {dt.text_muted}; font-size: 12px; background: transparent;"
        )
