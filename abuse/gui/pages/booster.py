"""Booster page — server boost tooling (UI stub)."""

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
    AppComboBox,
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


class BoosterPage(BasePage):
    """Server booster UI — bot logic not yet wired."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(
            "Booster",
            "Apply Nitro boosts to servers.",
            eyebrow="Booster",
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
            "Booster logic is not yet wired — this surface shows the planned UI only.",
            tone="preview",
        )
        body_layout.addWidget(self.status_banner)

        # ── Target card ───────────────────────────────────────────────────────
        target_card = PanelCard("Boost Target", "Select the server and boost parameters.")
        body_layout.addWidget(target_card)

        target_card.body_layout.addWidget(SectionLabel("Target Server"))
        self._server_input = AppLineEdit("Server ID or invite link")
        target_card.body_layout.addWidget(self._server_input)

        boost_row = QHBoxLayout()
        boost_row.setSpacing(24)

        count_col = QVBoxLayout()
        count_col.setSpacing(4)
        count_col.addWidget(SectionLabel("Boosts to apply"))
        self._boost_count = AppSpinBox()
        self._boost_count.setRange(1, 30)
        self._boost_count.setValue(2)
        count_col.addWidget(self._boost_count)
        boost_row.addLayout(count_col)

        delay_col = QVBoxLayout()
        delay_col.setSpacing(4)
        delay_col.addWidget(SectionLabel("Delay between boosts (ms)"))
        self._delay_spin = AppSpinBox()
        self._delay_spin.setRange(500, 30000)
        self._delay_spin.setSingleStep(500)
        self._delay_spin.setValue(1500)
        delay_col.addWidget(self._delay_spin)
        boost_row.addLayout(delay_col)

        boost_row.addStretch(1)
        target_card.body_layout.addLayout(boost_row)

        action_row = QHBoxLayout()
        action_row.setSpacing(12)
        self._start_btn = AppButton("Start Booster", "accent")
        self._start_btn.setEnabled(False)
        self._stop_btn = AppButton("Stop", "danger")
        self._stop_btn.setEnabled(False)
        action_row.addWidget(self._start_btn)
        action_row.addWidget(self._stop_btn)
        action_row.addStretch(1)
        target_card.body_layout.addLayout(action_row)

        # ── Token accounts card ───────────────────────────────────────────────
        tokens_card = PanelCard(
            "Nitro Accounts",
            "Accounts loaded from tokens.json that have an active Nitro subscription.",
        )
        body_layout.addWidget(tokens_card)

        self._empty_label = QLabel("No Nitro accounts detected.")
        self._empty_label.setObjectName("boosterEmpty")
        tokens_card.body_layout.addWidget(self._empty_label)

        # ── Stats card ────────────────────────────────────────────────────────
        stats_card = PanelCard("Session Stats")
        body_layout.addWidget(stats_card)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(32)

        for label, attr in (
            ("Applied", "_stat_applied"),
            ("Failed", "_stat_failed"),
            ("Accounts Used", "_stat_accounts"),
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
        for attr in ("_stat_applied", "_stat_failed", "_stat_accounts"):
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
