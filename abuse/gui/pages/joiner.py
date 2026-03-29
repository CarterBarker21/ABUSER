"""Joiner page — server auto-join tooling (UI stub)."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..components import (
    AppButton,
    AppLineEdit,
    AppSpinBox,
    InfoBanner,
    PanelCard,
    SectionLabel,
    StatusChip,
    rgba,
)
from ..theme import get_theme_manager
from .base import BasePage


class JoinerPage(BasePage):
    """Server auto-join UI — bot logic not yet wired."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(
            "Joiner",
            "Auto-join servers via invite links.",
            eyebrow="Joiner",
            parent=parent,
        )
        self.root_layout.removeWidget(self.header)
        self.header.hide()
        self._build_ui()

    def _build_ui(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(24, 24, 24, 24)
        body_layout.setSpacing(16)
        scroll.setWidget(body)
        self.root_layout.addWidget(scroll, 1)

        # ── Status banner ─────────────────────────────────────────────────────
        self.status_banner = InfoBanner(
            "Preview",
            "Joiner logic is not yet wired — this surface shows the planned UI only.",
            tone="preview",
        )
        body_layout.addWidget(self.status_banner)

        # ── Configuration card ────────────────────────────────────────────────
        config_card = PanelCard("Join Configuration", "Set up invite links and joining behaviour.")
        body_layout.addWidget(config_card)

        # Invite input row
        invite_row = QHBoxLayout()
        invite_row.setSpacing(12)
        self._invite_input = AppLineEdit("discord.gg/invite  or  full invite URL")
        add_btn = AppButton("Add", "primary")
        add_btn.setEnabled(False)
        invite_row.addWidget(self._invite_input, 1)
        invite_row.addWidget(add_btn)
        config_card.body_layout.addWidget(SectionLabel("Invite Link"))
        config_card.body_layout.addLayout(invite_row)

        # Delay row
        delay_row = QHBoxLayout()
        delay_row.setSpacing(12)
        self._delay_spin = AppSpinBox()
        self._delay_spin.setRange(500, 60000)
        self._delay_spin.setSingleStep(500)
        self._delay_spin.setValue(2000)
        delay_row.addWidget(self._delay_spin)
        delay_row.addStretch(1)
        config_card.body_layout.addWidget(SectionLabel("Delay between joins (ms)"))
        config_card.body_layout.addLayout(delay_row)

        # Action row
        action_row = QHBoxLayout()
        action_row.setSpacing(12)
        self._start_btn = AppButton("Start Joiner", "accent")
        self._start_btn.setEnabled(False)
        self._stop_btn = AppButton("Stop", "danger")
        self._stop_btn.setEnabled(False)
        action_row.addWidget(self._start_btn)
        action_row.addWidget(self._stop_btn)
        action_row.addStretch(1)
        config_card.body_layout.addLayout(action_row)

        # ── Invite list card ──────────────────────────────────────────────────
        list_card = PanelCard("Invite Queue", "Invites staged for joining.")
        body_layout.addWidget(list_card)

        self._empty_label = QLabel("No invites added yet.")
        self._empty_label.setObjectName("joinerEmpty")
        list_card.body_layout.addWidget(self._empty_label)

        # ── Stats card ────────────────────────────────────────────────────────
        stats_card = PanelCard("Session Stats")
        body_layout.addWidget(stats_card)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(32)

        for label, attr in (
            ("Joined", "_stat_joined"),
            ("Failed", "_stat_failed"),
            ("Pending", "_stat_pending"),
        ):
            col = QVBoxLayout()
            col.setSpacing(4)
            val = QLabel("0")
            lbl = QLabel(label)
            setattr(self, attr + "_val", val)
            setattr(self, attr + "_lbl", lbl)
            col.addWidget(val)
            col.addWidget(lbl)
            stats_row.addLayout(col)

        stats_row.addStretch(1)
        stats_card.body_layout.addLayout(stats_row)

        body_layout.addStretch(1)
        self.refresh_theme()

    def refresh_theme(self) -> None:
        super().refresh_theme()
        dt = get_theme_manager().design_tokens

        if hasattr(self, "_empty_label"):
            self._empty_label.setStyleSheet(
                f"color: {dt.text_muted}; font-size: 13px; background: transparent;"
            )
        for attr in ("_stat_joined", "_stat_failed", "_stat_pending"):
            val_w = getattr(self, attr + "_val", None)
            lbl_w = getattr(self, attr + "_lbl", None)
            if val_w:
                val_w.setStyleSheet(
                    f"color: {dt.text_primary}; font-size: 22px; font-weight: 700; background: transparent;"
                )
            if lbl_w:
                lbl_w.setStyleSheet(
                    f"color: {dt.text_muted}; font-size: 11px; font-weight: 600; "
                    f"letter-spacing: 0.8px; background: transparent;"
                )
