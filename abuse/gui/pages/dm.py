"""DM page with an honest local-only queue."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QSplitter,
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
        self._queue: list[dict[str, str | int]] = []
        self._build_ui()

    def _build_ui(self) -> None:
        self.root_layout.addWidget(
            InfoBanner(
                "Delivery unavailable",
                "This build keeps the DM composer and queue visible, but message delivery and bulk tools remain disabled instead of pretending to be wired.",
                tone="preview",
            )
        )

        splitter = QSplitter()
        splitter.setChildrenCollapsible(False)
        self.root_layout.addWidget(splitter, 1)

        compose_card = PanelCard("Message Composer", "Build a draft and stage it in the local queue.")
        splitter.addWidget(compose_card)

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(self.tokens.metrics.spacing_md)

        self.recipient_input = AppLineEdit("User ID or @username")
        form.addRow(SectionLabel("Recipient"), self.recipient_input)

        self.template_combo = AppComboBox()
        self.template_combo.addItems(["Custom Message", "Short Greeting", "Follow-up Note"])
        form.addRow(SectionLabel("Template"), self.template_combo)

        compose_card.body_layout.addLayout(form)

        self.message_input = AppTextEdit("Type your draft here")
        self.message_input.setMinimumHeight(220)
        self.message_input.textChanged.connect(self._update_character_count)
        compose_card.body_layout.addWidget(self.message_input)

        counts_row = QHBoxLayout()
        counts_row.setSpacing(self.tokens.metrics.spacing_md)

        self.count_spin = AppSpinBox()
        self.count_spin.setRange(1, 50)
        self.count_spin.setValue(1)

        self.delay_spin = AppSpinBox()
        self.delay_spin.setRange(250, 30000)
        self.delay_spin.setSingleStep(250)
        self.delay_spin.setValue(1000)

        counts_row.addWidget(QLabel("Count"))
        counts_row.addWidget(self.count_spin)
        counts_row.addSpacing(self.tokens.metrics.spacing_sm)
        counts_row.addWidget(QLabel("Delay (ms)"))
        counts_row.addWidget(self.delay_spin)
        counts_row.addStretch(1)

        self.character_count = QLabel("0 / 2000")
        counts_row.addWidget(self.character_count)
        compose_card.body_layout.addLayout(counts_row)

        action_row = QHBoxLayout()
        action_row.setSpacing(self.tokens.metrics.spacing_md)
        self.queue_button = AppButton("Add to Queue", "secondary")
        self.queue_button.clicked.connect(self._add_to_queue)
        action_row.addWidget(self.queue_button)

        self.send_button = AppButton("Send Unavailable", "preview")
        self.send_button.setEnabled(False)
        action_row.addWidget(self.send_button)
        compose_card.body_layout.addLayout(action_row)

        queue_card = PanelCard("Send Queue", "Review locally staged drafts and clear them when needed.")
        splitter.addWidget(queue_card)

        self.queue_stack = QStackedWidget()
        self.queue_empty = EmptyState("Queue is empty", "Drafts added from the composer will appear here for local review.")
        self.queue_stack.addWidget(self.queue_empty)

        self.queue_list = QListWidget()
        self.queue_stack.addWidget(self.queue_list)
        queue_card.body_layout.addWidget(self.queue_stack)

        queue_controls = QHBoxLayout()
        queue_controls.setSpacing(self.tokens.metrics.spacing_md)
        self.queue_count_label = QLabel("0 queued")
        queue_controls.addWidget(self.queue_count_label)
        queue_controls.addStretch(1)
        clear_button = AppButton("Clear Queue", "tertiary")
        clear_button.clicked.connect(self._clear_queue)
        queue_controls.addWidget(clear_button)
        queue_card.body_layout.addLayout(queue_controls)

        quick_tools = PanelCard("Secondary Tools", "Visible for interface completeness and clearly marked as unavailable.")
        tools_layout = QVBoxLayout()
        tools_layout.setSpacing(self.tokens.metrics.spacing_md)
        for label in (
            "Mass DM Friends",
            "Mass DM Guild",
            "DM Advertise",
            "Close All DMs",
            "Clear DMs",
            "DM Spammer",
        ):
            tile = ActionTileButton(label, "Unavailable in this build.", variant="preview")
            tile.setEnabled(False)
            tools_layout.addWidget(tile)
        quick_tools.body_layout.addLayout(tools_layout)
        queue_card.body_layout.addWidget(quick_tools)

        splitter.setSizes([700, 420])
        self.refresh_theme()
        self._update_queue_view()

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
            if len(draft["message"]) > 60:
                preview += "…"
            item = QListWidgetItem(
                f"{draft['recipient']}  |  {draft['count']}x @ {draft['delay']} ms\n{preview}"
            )
            self.queue_list.addItem(item)

        has_items = bool(self._queue)
        self.queue_stack.setCurrentWidget(self.queue_list if has_items else self.queue_empty)
        self.queue_count_label.setText(f"{len(self._queue)} queued")

    def refresh_theme(self) -> None:
        super().refresh_theme()
        dt = get_theme_manager().design_tokens
        self.queue_list.setStyleSheet(
            f"""
            QListWidget {{
                background-color: {dt.surface_raised};
                color: {dt.text_primary};
                border: 1px solid {dt.border};
                border-radius: 12px;
                padding: 6px;
            }}
            QListWidget::item {{
                padding: 10px 12px;
                margin: 4px 0;
                border-bottom: 1px solid {dt.border};
            }}
            """
        )
        self.queue_count_label.setStyleSheet(f"color: {dt.text_secondary};")
        self.character_count.setStyleSheet(f"color: {dt.text_muted}; font-size: 12px;")
