"""Runtime log viewer."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import QFileDialog, QHBoxLayout, QTextEdit, QVBoxLayout, QWidget, QStackedWidget

from ..components import AppButton, AppComboBox, EmptyState, PanelCard, SearchField, ToggleSwitch
from ..theme import get_theme_manager
from .base import BasePage


class LogsPage(BasePage):

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(
            "Logs",
            "Filter runtime output by level and search terms without drowning the toolbar in color noise.",
            eyebrow="Console",
            parent=parent,
        )
        self._entries: list[dict[str, str]] = []
        self._build_ui()

    def _level_color(self, level: str) -> str:
        dt = get_theme_manager().design_tokens
        return {
            "DEBUG": dt.text_disabled,
            "INFO": dt.text_primary,
            "WARNING": dt.warning,
            "ERROR": dt.danger,
            "CRITICAL": dt.danger,
        }.get(level.upper(), dt.text_muted)

    def _build_ui(self) -> None:
        toolbar = PanelCard("Log Controls", "Trim what you see, keep auto-scroll optional, and export when needed.")
        toolbar_row = QHBoxLayout()
        toolbar_row.setSpacing(self.tokens.metrics.spacing_md)

        self.search_input = SearchField("Filter log text")
        self.search_input.textChanged.connect(self._render_logs)
        toolbar_row.addWidget(self.search_input, 1)

        self.level_combo = AppComboBox()
        self.level_combo.addItems(["All", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.level_combo.currentTextChanged.connect(self._render_logs)
        toolbar_row.addWidget(self.level_combo)

        self.auto_scroll = ToggleSwitch("Auto-scroll")
        self.auto_scroll.setChecked(True)
        toolbar_row.addWidget(self.auto_scroll)

        clear_button = AppButton("Clear", "tertiary")
        clear_button.clicked.connect(self.clear_logs)
        toolbar_row.addWidget(clear_button)

        export_button = AppButton("Export", "secondary")
        export_button.clicked.connect(self._export_logs)
        toolbar_row.addWidget(export_button)

        toolbar.body_layout.addLayout(toolbar_row)
        self.root_layout.addWidget(toolbar)

        console_card = PanelCard("Runtime Console", "Incoming bot logs are stored in memory and re-rendered through the active filters.")
        self.stack = QStackedWidget()
        self.empty_state = EmptyState("No logs yet", "Logs will appear here when the runtime starts emitting output.")
        self.stack.addWidget(self.empty_state)

        self.logs_view = QTextEdit()
        self.logs_view.setReadOnly(True)
        self.stack.addWidget(self.logs_view)
        console_card.body_layout.addWidget(self.stack)

        footer = QHBoxLayout()
        self.count_label = QWidget()
        self.count_layout = QHBoxLayout(self.count_label)
        self.count_layout.setContentsMargins(0, 0, 0, 0)
        self.count_value = AppButton("0 entries", "preview")
        self.count_value.setEnabled(False)
        self.count_layout.addWidget(self.count_value)
        footer.addWidget(self.count_label)
        footer.addStretch(1)
        console_card.body_layout.addLayout(footer)

        self.root_layout.addWidget(console_card, 1)
        self.refresh_theme()

    def add_log(self, timestamp: str, name: str, level: str, message: str) -> None:
        self._entries.append(
            {"timestamp": timestamp, "name": name, "level": level.upper(), "message": message}
        )
        self._render_logs()

    def clear_logs(self) -> None:
        self._entries.clear()
        self._render_logs()

    def _filtered_entries(self) -> list[dict[str, str]]:
        level = self.level_combo.currentText()
        search = self.search_input.text().lower().strip()
        entries = self._entries
        if level != "All":
            entries = [entry for entry in entries if entry["level"] == level]
        if search:
            entries = [
                entry
                for entry in entries
                if search in entry["message"].lower()
                or search in entry["name"].lower()
                or search in entry["level"].lower()
            ]
        return entries

    def _render_logs(self) -> None:
        entries = self._filtered_entries()
        self.count_value.setText(f"{len(entries)} entries")
        if not entries:
            self.stack.setCurrentWidget(self.empty_state)
            return

        dt = get_theme_manager().design_tokens
        rows = []
        for entry in entries:
            level_color = self._level_color(entry["level"])
            rows.append(
                (
                    "<div style='margin-bottom:6px;'>"
                    f"<span style='color:{dt.text_muted};'>[{html.escape(entry['timestamp'])}]</span> "
                    f"<span style='color:{level_color}; font-weight:700;'>{html.escape(entry['level'])}</span> "
                    f"<span style='color:{dt.text_secondary};'>{html.escape(entry['name'])}</span> "
                    f"<span style='color:{dt.text_primary};'>{html.escape(entry['message'])}</span>"
                    "</div>"
                )
            )
        self.logs_view.setHtml("<body style='font-family: Consolas, monospace;'>" + "".join(rows) + "</body>")
        self.stack.setCurrentWidget(self.logs_view)
        if self.auto_scroll.isChecked():
            scrollbar = self.logs_view.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def _export_logs(self) -> None:
        entries = self._filtered_entries()
        if not entries:
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Export Logs", str(Path.cwd() / "abuse_logs.txt"), "Text Files (*.txt)")
        if not filename:
            return
        with open(filename, "w", encoding="utf-8") as handle:
            for entry in entries:
                handle.write(f"[{entry['timestamp']}] {entry['level']} {entry['name']} {entry['message']}\n")

    def refresh_theme(self) -> None:
        super().refresh_theme()
        dt = get_theme_manager().design_tokens
        self.logs_view.setStyleSheet(
            f"""
            QTextEdit {{
                background-color: {dt.background};
                color: {dt.text_primary};
                border: 1px solid {dt.border};
                border-radius: 12px;
                padding: 12px;
            }}
            """
        )
        self.count_value.refresh_theme()
        self._render_logs()
