"""Token Finder Thread for the ABUSER GUI.

Provides a QThread-based implementation for searching local Discord installations
for authentication tokens without blocking the GUI.
"""

from __future__ import annotations

from typing import List, Tuple

from PyQt6.QtCore import QThread, pyqtSignal


class TokenFinderThread(QThread):
    """Background thread for finding Discord tokens in local storage.
    
    This thread searches common Discord installation directories for valid
    authentication tokens. It runs asynchronously to avoid freezing the GUI.
    
    Signals:
        tokens_found: Emitted when tokens are found. List of (source, token) tuples.
        no_tokens_found: Emitted when no tokens are found after searching.
        error: Emitted when an error occurs during token finding.
        finished: Emitted when the thread completes (inherited from QThread).
    
    Example:
        >>> thread = TokenFinderThread()
        >>> thread.tokens_found.connect(on_tokens_found)
        >>> thread.no_tokens_found.connect(on_no_tokens)
        >>> thread.error.connect(on_error)
        >>> thread.start()  # Non-blocking
    """
    
    tokens_found = pyqtSignal(list)  # List of (source, token) tuples
    no_tokens_found = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """Initialize the token finder thread.
        
        Args:
            parent: The parent QObject (optional).
        """
        super().__init__(parent)
        self._tokens: List[Tuple[str, str]] = []
    
    def run(self) -> None:
        """Execute the token search in a background thread.
        
        This method is called when start() is invoked. It imports the
        token finder utility and searches for Discord tokens in local
        storage locations.
        """
        try:
            # Import here to avoid issues if the module isn't available
            from abuse.utils.token_finder import TokenFinder
            
            finder = TokenFinder()
            found_tokens = finder.find_tokens()
            
            # find_tokens returns List[Tuple[str, str]] as (client_name, token)
            if found_tokens:
                self._tokens = found_tokens
                self.tokens_found.emit(found_tokens)
            else:
                self.no_tokens_found.emit()
                
        except ImportError as e:
            self.error.emit(f"Token finder module not available: {e}")
        except Exception as e:
            self.error.emit(f"Error searching for tokens: {e}")
    
    @property
    def tokens(self) -> List[Tuple[str, str]]:
        """Get the tokens found during the last search.
        
        Returns:
            A list of tuples containing (source_name, token_string).
        """
        return self._tokens
