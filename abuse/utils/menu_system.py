"""
Menu System for ABUSER Bot
Provides interactive terminal menus with navigation
"""

import sys
import shutil
from typing import List, Dict, Callable, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from colorama import Fore, Style


class MenuAction(Enum):
    """Menu action types"""
    SUBMENU = "submenu"
    CALLBACK = "callback"
    BACK = "back"
    EXIT = "exit"


@dataclass
class MenuItem:
    """Single menu item"""
    label: str
    action: MenuAction
    value: Any = None
    description: str = ""
    disabled: bool = False
    hidden: bool = False


@dataclass
class Menu:
    """Menu definition"""
    title: str
    items: List[MenuItem] = field(default_factory=list)
    parent: Optional['Menu'] = None
    show_back: bool = True
    custom_header: Optional[str] = None
    custom_footer: Optional[str] = None


class MenuSystem:
    """
    Interactive menu system for terminal UI
    Handles navigation, rendering, and user input
    """
    
    # Box drawing characters
    H_LINE = "═"
    V_LINE = "║"
    TOP_LEFT = "╔"
    TOP_RIGHT = "╗"
    BOTTOM_LEFT = "╚"
    BOTTOM_RIGHT = "╝"
    T_LEFT = "╠"
    T_RIGHT = "╣"
    
    def __init__(self, width: int = 58):
        self.width = width
        self.menu_stack: List[Menu] = []
        self.current_menu: Optional[Menu] = None
        self.running = False
        self.exit_callback: Optional[Callable] = None
        self._clear_on_render = True
        
    def _clear_screen(self):
        """Clear terminal screen"""
        sys.stdout.write('\033[2J\033[H')
        sys.stdout.flush()
        
    def _center_text(self, text: str, width: int = None) -> str:
        """Center text within given width"""
        if width is None:
            width = self.width - 2
        text = str(text)
        if len(text) >= width:
            return text[:width]
        padding = (width - len(text)) // 2
        return " " * padding + text + " " * (width - len(text) - padding)
        
    def _pad_text(self, text: str, width: int = None) -> str:
        """Pad text to fill width"""
        if width is None:
            width = self.width - 2
        text = str(text)
        if len(text) >= width:
            return text[:width]
        return text + " " * (width - len(text))
        
    def _render_box_line(self, text: str = "", align: str = "left", 
                         left: str = V_LINE, right: str = V_LINE,
                         color: str = Fore.CYAN) -> str:
        """Render a line inside the box"""
        inner_width = self.width - 2
        if align == "center":
            content = self._center_text(text, inner_width)
        elif align == "right":
            content = text.rjust(inner_width)
        else:
            content = self._pad_text(text, inner_width)
        return f"{color}{left}{Fore.WHITE}{content}{color}{right}{Style.RESET_ALL}"
        
    def _render_separator(self, left: str = T_LEFT, right: str = T_RIGHT,
                          color: str = Fore.CYAN) -> str:
        """Render horizontal separator line"""
        return f"{color}{left}{self.H_LINE * (self.width - 2)}{right}{Style.RESET_ALL}"
        
    def _render_top_border(self, color: str = Fore.CYAN) -> str:
        """Render top border"""
        return f"{color}{self.TOP_LEFT}{self.H_LINE * (self.width - 2)}{self.TOP_RIGHT}{Style.RESET_ALL}"
        
    def _render_bottom_border(self, color: str = Fore.CYAN) -> str:
        """Render bottom border"""
        return f"{color}{self.BOTTOM_LEFT}{self.H_LINE * (self.width - 2)}{self.BOTTOM_RIGHT}{Style.RESET_ALL}"
        
    def _render_banner(self) -> str:
        """Render ABUSER banner"""
        return f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════╗
║                                                          ║
║     {Fore.WHITE}█████╗ ██████╗ ██╗   ██╗███████╗███████╗██████╗{Fore.CYAN}     ║
║     {Fore.WHITE}██╔══██╗██╔══██╗██║   ██║██╔════╝██╔════╝██╔══██╗{Fore.CYAN}    ║
║     {Fore.WHITE}███████║██████╔╝██║   ██║███████╗█████╗  ██████╔╝{Fore.CYAN}    ║
║     {Fore.WHITE}██╔══██║██╔══██╗██║   ██║╚════██║██╔══╝  ██╔══██╗{Fore.CYAN}    ║
║     {Fore.WHITE}██║  ██║██████╔╝╚██████╔╝███████║███████╗██║  ██║{Fore.CYAN}    ║
║     {Fore.WHITE}╚═╝  ╚═╝╚═════╝  ╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═╝{Fore.CYAN}    ║
║                                                          ║
║              {Fore.WHITE}Advanced Bot for User Server                {Fore.CYAN}║
║                 {Fore.WHITE}Enhancement & Raiding{Fore.CYAN}                    ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}"""

    def render_menu(self, menu: Menu):
        """Render a complete menu"""
        if self._clear_on_render:
            self._clear_screen()
            
        lines = []
        
        # Banner
        lines.append(self._render_banner())
        lines.append("")
        
        # Custom header if provided
        if menu.custom_header:
            lines.append(menu.custom_header)
            lines.append("")
            
        # Menu title box
        lines.append(self._render_top_border())
        lines.append(self._render_box_line(menu.title.upper(), align="center"))
        lines.append(self._render_separator())
        
        # Menu items
        visible_items = [item for item in menu.items if not item.hidden]
        for i, item in enumerate(visible_items, 1):
            if item.disabled:
                line = f"  {Fore.LIGHTBLACK_EX}{i}. {item.label}{Style.RESET_ALL}"
                if item.description:
                    line += f" {Fore.LIGHTBLACK_EX}({item.description}){Style.RESET_ALL}"
            else:
                line = f"  {Fore.YELLOW}{i}.{Fore.WHITE} {item.label}{Style.RESET_ALL}"
                if item.description:
                    line += f" {Fore.LIGHTBLACK_EX}- {item.description}{Style.RESET_ALL}"
            lines.append(self._render_box_line(line))
            
        # Back option
        if menu.show_back and menu.parent is not None:
            lines.append(self._render_separator())
            back_num = len(visible_items) + 1
            lines.append(self._render_box_line(f"  {Fore.YELLOW}0.{Fore.WHITE} ← Back{Style.RESET_ALL}"))
        elif menu.show_back and not menu.parent:
            lines.append(self._render_separator())
            lines.append(self._render_box_line(f"  {Fore.YELLOW}0.{Fore.WHITE} Exit{Style.RESET_ALL}"))
            
        lines.append(self._render_bottom_border())
        
        # Custom footer
        if menu.custom_footer:
            lines.append("")
            lines.append(menu.custom_footer)
            
        # Print everything
        print("\n".join(lines))
        
    def get_input(self, menu: Menu) -> Optional[MenuItem]:
        """Get user input and return selected item"""
        visible_items = [item for item in menu.items if not item.hidden]
                
        while True:
            try:
                choice = input(f"\n{Fore.CYAN}[?]{Fore.WHITE} Select option: {Style.RESET_ALL}").strip()
                
                if not choice:
                    continue
                    
                try:
                    num = int(choice)
                except ValueError:
                    print(f"{Fore.RED}[!]{Fore.WHITE} Please enter a number{Style.RESET_ALL}")
                    continue
                    
                # Handle back/exit (0)
                if num == 0:
                    if menu.parent is not None:
                        return MenuItem("Back", MenuAction.BACK)
                    else:
                        return MenuItem("Exit", MenuAction.EXIT)
                        
                # Handle menu items
                if 1 <= num <= len(visible_items):
                    selected = visible_items[num - 1]
                    if selected.disabled:
                        print(f"{Fore.RED}[!]{Fore.WHITE} This option is disabled{Style.RESET_ALL}")
                        continue
                    return selected
                else:
                    print(f"{Fore.RED}[!]{Fore.WHITE} Invalid option. Try again.{Style.RESET_ALL}")
                    
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}[!] Use option 0 to exit{Style.RESET_ALL}")
                continue
                
    def navigate_to(self, menu: Menu):
        """Navigate to a submenu"""
        if self.current_menu:
            self.menu_stack.append(self.current_menu)
        menu.parent = self.current_menu
        self.current_menu = menu
        
    def go_back(self) -> bool:
        """Go back to parent menu. Returns False if no parent."""
        if self.menu_stack:
            self.current_menu = self.menu_stack.pop()
            return True
        else:
            self.current_menu = None
            return False
            
    def run_menu(self, menu: Menu, parent: Optional[Menu] = None) -> Any:
        """
        Run a menu and handle navigation
        Returns: 
            - The result value if a callback returns something
            - 'BACK' sentinel if user pressed back (caller should handle)
            - 'EXIT' sentinel if user chose to exit
            - None for normal flow (submenu completed, etc.)
        """
        # Sentinel values for navigation
        BACK_SENTINEL = "__MENU_BACK__"
        EXIT_SENTINEL = "__MENU_EXIT__"
        
        menu.parent = parent
        self.current_menu = menu
        
        while True:
            self.render_menu(self.current_menu)
            selected = self.get_input(self.current_menu)
            
            if selected is None:
                continue
                
            if selected.action == MenuAction.BACK:
                # User pressed back - return sentinel to let caller handle
                return BACK_SENTINEL
                    
            elif selected.action == MenuAction.EXIT:
                # Exit completely
                self.current_menu = None
                return EXIT_SENTINEL
                
            elif selected.action == MenuAction.SUBMENU:
                if isinstance(selected.value, Menu):
                    # Run submenu recursively
                    submenu_result = self.run_menu(selected.value, self.current_menu)
                    
                    # Handle submenu navigation results
                    if submenu_result == EXIT_SENTINEL:
                        # User exited from submenu - propagate exit
                        self.current_menu = None
                        return EXIT_SENTINEL
                    elif submenu_result == BACK_SENTINEL:
                        # User went back from submenu - just continue showing current menu
                        continue
                    elif submenu_result is not None:
                        # Submenu callback returned a value - propagate it
                        return submenu_result
                    # Otherwise submenu completed normally, continue showing current menu
                    continue
                        
            elif selected.action == MenuAction.CALLBACK:
                if callable(selected.value):
                    try:
                        result = selected.value()
                        if result is not None:
                            # Callback wants to return a value (e.g., _start_bot returns True)
                            return result
                        # Callback completed without result - refresh menu to show state changes
                        continue
                    except Exception as e:
                        print(f"{Fore.RED}[!] Error: {e}{Style.RESET_ALL}")
                        input(f"\n{Fore.CYAN}[Press Enter to continue...]{Style.RESET_ALL}")
                        continue
                        
        return None
        
    def confirm(self, message: str, default: bool = False) -> bool:
        """Show a confirmation dialog"""
        default_str = "Y/n" if default else "y/N"
        prompt = f"\n{Fore.CYAN}[?]{Fore.WHITE} {message} [{default_str}]: {Style.RESET_ALL}"
        
        while True:
            response = input(prompt).strip().lower()
            
            if not response:
                return default
            elif response in ('y', 'yes'):
                return True
            elif response in ('n', 'no'):
                return False
            else:
                print(f"{Fore.RED}[!] Please enter 'y' or 'n'{Style.RESET_ALL}")


# Utility functions for creating common menu patterns

def create_submenu_item(label: str, submenu: Menu, description: str = "") -> MenuItem:
    """Create a submenu navigation item"""
    return MenuItem(
        label=label,
        action=MenuAction.SUBMENU,
        value=submenu,
        description=description
    )
    

def create_callback_item(label: str, callback: Callable, description: str = "") -> MenuItem:
    """Create a callback action item"""
    return MenuItem(
        label=label,
        action=MenuAction.CALLBACK,
        value=callback,
        description=description
    )


def create_disabled_item(label: str, description: str = "") -> MenuItem:
    """Create a disabled menu item"""
    return MenuItem(
        label=label,
        action=MenuAction.CALLBACK,
        value=lambda: None,
        description=description,
        disabled=True
    )
