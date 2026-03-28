"""Login page for the refactored GUI."""

from __future__ import annotations

from typing import List, Optional, Tuple

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..components import (
    AppButton,
    AppComboBox,
    AppLineEdit,
    InfoBanner,
    PanelCard,
    SectionLabel,
    ToggleSwitch,
    refresh_themed_tree,
)
from ..config import (
    clear_remembered_sessions,
    get_latest_session,
    load_gui_config,
    load_remembered_sessions,
    mask_token,
    save_remembered_session,
)
from ..token_finder_thread import TokenFinderThread
from .base import BasePage


class LoginPage(BasePage):
    login_requested = pyqtSignal(str)
    logout_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(
            "Login",
            "Connect with a token, review remembered sessions, and keep the session flow explicit.",
            eyebrow="Session",
            parent=parent,
        )
        self.root_layout.removeWidget(self.header)
        self.header.hide()
        self._connected = False
        self._save_tokens_allowed = True
        self._current_status_tone = "neutral"
        self._found_tokens: List[Tuple[str, str]] = []
        self._token_finder_thread: Optional[TokenFinderThread] = None
        self._build_ui()
        self.load_saved_tokens()

    def _build_ui(self) -> None:
        scroll, wrapper, body_layout = self.create_scroll_body(max_width=960)
        
        # Make wrapper expand to fill scroll area for vertical centering
        wrapper.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        
        self.root_layout.addWidget(scroll, 1)

        # Add stretch before card to push it to center
        body_layout.addStretch(1)

        self.auth_card = PanelCard("Discord Token")
        self.auth_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        body_layout.addWidget(self.auth_card)

        self.token_input = AppLineEdit("Paste your token here")
        self.token_input.setEchoMode(AppLineEdit.EchoMode.Password)
        self.auth_card.body_layout.addWidget(self.token_input)

        saved_label = SectionLabel("Remembered Sessions")
        self.saved_session_combo = AppComboBox()
        self.saved_session_combo.currentIndexChanged.connect(self._on_saved_session_changed)
        self.auth_card.body_layout.addWidget(saved_label)
        self.auth_card.body_layout.addWidget(self.saved_session_combo)

        controls_row = QHBoxLayout()
        controls_row.setSpacing(self.tokens.metrics.spacing_md)

        self.show_toggle = ToggleSwitch("Show token")
        self.show_toggle.toggled.connect(self._on_show_toggle_changed)
        controls_row.addWidget(self.show_toggle)

        self.remember_toggle = ToggleSwitch("Remember session locally")
        controls_row.addWidget(self.remember_toggle)
        controls_row.addStretch(1)

        self.auto_find_button = AppButton("Auto Find Token", "secondary")
        self.auto_find_button.setToolTip("Scan local Discord installations for saved tokens (Windows only).")
        self.auto_find_button.setEnabled(True)
        self.auto_find_button.clicked.connect(self._on_auto_find_clicked)
        controls_row.addWidget(self.auto_find_button)
        self.auth_card.body_layout.addLayout(controls_row)
        
        # Found tokens dropdown (hidden by default)
        self.found_tokens_row = QHBoxLayout()
        self.found_tokens_row.setSpacing(self.tokens.metrics.spacing_md)
        self.found_tokens_row.setContentsMargins(0, 8, 0, 0)
        
        self.found_tokens_label = SectionLabel("Found Tokens")
        self.found_tokens_combo = AppComboBox()
        self.found_tokens_combo.currentIndexChanged.connect(self._on_found_token_selected)
        
        self.found_tokens_row.addWidget(self.found_tokens_label)
        self.found_tokens_row.addWidget(self.found_tokens_combo, 1)
        self.auth_card.body_layout.addLayout(self.found_tokens_row)
        
        # Hide the found tokens row initially
        self._set_found_tokens_visible(False)

        self.primary_button = AppButton("Connect", "primary")
        self.primary_button.clicked.connect(self._on_primary_clicked)
        self.auth_card.body_layout.addWidget(self.primary_button)

        self.status_banner = InfoBanner(
            "Ready to connect",
            "Nothing is running yet. Enter a token and start the session when you are ready.",
            tone="neutral",
        )
        self.auth_card.body_layout.addWidget(self.status_banner)

        self.storage_note = QLabel("")
        self.auth_card.body_layout.addWidget(self.storage_note)

        body_layout.addStretch(1)
        self.refresh_theme()

    @property
    def is_connected(self) -> bool:
        return self._connected

    def _update_storage_note(self) -> None:
        if self._save_tokens_allowed:
            text = "Remembered sessions are stored locally in data/tokens.json when the checkbox is enabled."
        else:
            text = "Saving new remembered sessions is disabled by the Privacy setting."
        self.storage_note.setText(text)

    def _populate_saved_sessions(self) -> None:
        current_token = self.saved_session_combo.currentData()
        self.saved_session_combo.blockSignals(True)
        self.saved_session_combo.clear()
        self.saved_session_combo.addItem("No remembered sessions", None)
        for account in load_remembered_sessions():
            label = account.get("name") or "Saved account"
            self.saved_session_combo.addItem(f"{label} ({mask_token(account['token'])})", account["token"])

        target_index = 0
        if current_token:
            for index in range(self.saved_session_combo.count()):
                if self.saved_session_combo.itemData(index) == current_token:
                    target_index = index
                    break

        self.saved_session_combo.setCurrentIndex(target_index)
        self.saved_session_combo.setEnabled(self.saved_session_combo.count() > 1)
        self.saved_session_combo.blockSignals(False)

    def set_privacy_options(self, save_tokens_enabled: bool) -> None:
        self._save_tokens_allowed = save_tokens_enabled
        self.remember_toggle.setEnabled(save_tokens_enabled)
        if not save_tokens_enabled:
            self.remember_toggle.setChecked(False)
        self._update_storage_note()

    def _on_show_toggle_changed(self, checked: bool) -> None:
        self.token_input.setEchoMode(
            AppLineEdit.EchoMode.Normal if checked else AppLineEdit.EchoMode.Password
        )

    def _on_saved_session_changed(self, index: int) -> None:
        token = self.saved_session_combo.itemData(index)
        if not token:
            return
        self.token_input.setText(token)
        self._set_status("Remembered session loaded", "The selected saved token was loaded into the input field.", "accent")

    def _forget_sessions(self) -> None:
        clear_remembered_sessions()
        self._populate_saved_sessions()
        self._set_status("Saved sessions cleared", "Local remembered sessions were removed from disk.", "neutral")

    def _set_found_tokens_visible(self, visible: bool) -> None:
        """Show or hide the found tokens dropdown."""
        self.found_tokens_label.setVisible(visible)
        self.found_tokens_combo.setVisible(visible)

    def _on_auto_find_clicked(self) -> None:
        """Handle the Auto Find button click."""
        # Check if we're on Windows
        import sys
        if sys.platform != "win32":
            self._set_status(
                "Auto Find unavailable",
                "Token auto-finding is only supported on Windows.",
                "warning"
            )
            return
        
        # Disable the button during search
        self.auto_find_button.setEnabled(False)
        self.auto_find_button.setText("Searching...")
        self._set_status(
            "Searching for tokens",
            "Scanning local Discord installations for authentication tokens...",
            "warning"
        )
        
        # Create and start the token finder thread
        self._token_finder_thread = TokenFinderThread(self)
        self._token_finder_thread.tokens_found.connect(self._on_tokens_found)
        self._token_finder_thread.no_tokens_found.connect(self._on_no_tokens_found)
        self._token_finder_thread.error.connect(self._on_token_finder_error)
        self._token_finder_thread.finished.connect(self._on_token_finder_finished)
        self._token_finder_thread.start()

    def _on_tokens_found(self, tokens: List[Tuple[str, str]]) -> None:
        """Handle found tokens from the token finder thread.
        
        Args:
            tokens: List of (source, token) tuples where source is the Discord client name.
        """
        self._found_tokens = tokens
        
        # Populate the dropdown
        self.found_tokens_combo.clear()
        self.found_tokens_combo.addItem("Select a token...", None)
        
        for source, token in tokens:
            # Mask the token for display: show first 10 and last 5 characters
            masked = f"{token[:10]}...{token[-5:]}" if len(token) > 15 else token
            display_text = f"{source}: {masked}"
            self.found_tokens_combo.addItem(display_text, token)
        
        # Show the dropdown
        self._set_found_tokens_visible(True)
        
        # Update status
        token_count = len(tokens)
        self._set_status(
            f"Found {token_count} token{'s' if token_count > 1 else ''}",
            "Select a token from the dropdown below to use it.",
            "success"
        )

    def _on_no_tokens_found(self) -> None:
        """Handle when no tokens are found."""
        self._set_found_tokens_visible(False)
        self._set_status(
            "No tokens found",
            "No valid Discord tokens were found. Make sure Discord is installed and you're logged in.",
            "neutral"
        )

    def _on_token_finder_error(self, error_message: str) -> None:
        """Handle errors from the token finder thread.
        
        Args:
            error_message: The error message to display.
        """
        self._set_found_tokens_visible(False)
        self._set_status(
            "Auto Find failed",
            error_message,
            "danger"
        )

    def _on_token_finder_finished(self) -> None:
        """Handle token finder thread completion."""
        # Re-enable the button
        self.auto_find_button.setEnabled(True)
        self.auto_find_button.setText("Auto Find Token")

    def _on_found_token_selected(self, index: int) -> None:
        """Handle selection of a token from the found tokens dropdown.
        
        Args:
            index: The selected index in the dropdown.
        """
        if index <= 0:  # First item is "Select a token..."
            return
        
        token = self.found_tokens_combo.itemData(index)
        if token:
            self.token_input.setText(token)
            self._set_status(
                "Token selected",
                "The selected token has been entered into the token field.",
                "accent"
            )

    def _on_primary_clicked(self) -> None:
        if self._connected:
            self.set_busy(True, "Stopping session", "Disconnecting from Discord and cleaning up the local runtime.")
            self.logout_requested.emit()
            return

        token = self.token_input.text().strip()
        if not token:
            self.show_error("Enter a token before connecting.")
            return

        self.set_busy(True, "Starting session", "Opening a bot session. The Guilds page will become available after login succeeds.")
        self.login_requested.emit(token)

    def set_busy(self, busy: bool, title: str = "", message: str = "") -> None:
        if busy:
            self.primary_button.setEnabled(False)
            self.token_input.setEnabled(False)
            self.saved_session_combo.setEnabled(False)
            self.show_toggle.setEnabled(False)
            self.remember_toggle.setEnabled(False)
            self.auto_find_button.setEnabled(False)
            self._set_status(title or "Working", message or "Please wait...", "warning")
            return

        self.primary_button.setEnabled(True)
        self.token_input.setEnabled(not self._connected)
        self.saved_session_combo.setEnabled((self.saved_session_combo.count() > 1) and (not self._connected))
        self.show_toggle.setEnabled(not self._connected)
        self.remember_toggle.setEnabled(self._save_tokens_allowed and not self._connected)
        self.auto_find_button.setEnabled(True)

    def _set_status(self, title: str, message: str, tone: str) -> None:
        self._current_status_tone = tone
        self.status_banner.title_label.setText(title)
        self.status_banner.message_label.setText(message)
        self.status_banner._tone = tone
        self.status_banner.refresh_theme()
        if tone == "success":
            self.header.set_status("Connected", "success")
        elif tone == "warning":
            self.header.set_status("Busy", "warning")
        elif tone == "danger":
            self.header.set_status("Attention", "danger")
        else:
            self.header.set_status("Idle", "neutral")

    def show_error(self, message: str) -> None:
        self._connected = False
        self.primary_button.setText("Connect")
        self.primary_button.set_variant("primary")
        self.set_busy(False)
        self._set_status("Connection failed", message, "danger")

    def on_login_success(self, username: str) -> None:
        self._connected = True
        self.primary_button.setText("Disconnect")
        self.primary_button.set_variant("danger")
        self.set_busy(False)
        self._set_status(
            "Connected",
            f"Signed in as {username}. Guilds, logs, and runtime state are now live.",
            "success",
        )

    def on_logout(self) -> None:
        self._connected = False
        self.primary_button.setText("Connect")
        self.primary_button.set_variant("primary")
        self.set_busy(False)
        self._set_status("Disconnected", "The session has ended. You can connect again at any time.", "neutral")

    def save_token_if_requested(self, token: str, username: str = "Unknown") -> None:
        if self._save_tokens_allowed and self.remember_toggle.isChecked():
            save_remembered_session(token, username)
            self._populate_saved_sessions()

    def load_saved_tokens(self) -> None:
        config = load_gui_config()
        self.set_privacy_options(config.get("privacy", {}).get("save_tokens", True))
        self.remember_toggle.setChecked(self._save_tokens_allowed)
        self._populate_saved_sessions()

        latest = get_latest_session()
        if latest:
            self.token_input.setText(latest["token"])
            self._set_status(
                "Remembered session loaded",
                f"{latest.get('name', 'Saved account')} was loaded from the local session store.",
                "accent",
            )
        else:
            self._set_status("Ready to connect", "No remembered session was found. Paste a token to continue.", "neutral")

        self.set_busy(False)

    def refresh_theme(self) -> None:
        super().refresh_theme()
        self.auth_card.refresh_theme()
        self.show_toggle.refresh_theme()
        self.remember_toggle.refresh_theme()
        self.auto_find_button.refresh_theme()
        self.primary_button.refresh_theme()
        self.saved_session_combo.refresh_theme()
        self.token_input.refresh_theme()
        self.status_banner.refresh_theme()
        self.found_tokens_combo.refresh_theme()
        self.storage_note.setStyleSheet(f"color: {self.theme.text_muted}; font-size: 12px;")
        refresh_themed_tree(self)
