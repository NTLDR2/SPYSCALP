#!/usr/bin/env python
# encoding: utf-8
"""
SPYSCALP - Final Version
Features: Persistent Header, TOML Configuration, File Browser UI
"""

import sqlite3
import logging
import os
from pathlib import Path
from datetime import datetime
from textual.app import App, ComposeResult
from textual.widgets import Footer, Static, Button, DataTable, Label, DirectoryTree
from textual.containers import Horizontal, Vertical, Container
from textual.binding import Binding
from textual.screen import Screen

# Setup logging
logging.basicConfig(
    filename='spyscalp_debug.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

VERSION = "1.0.0"

class ConfigManager:
    """Manages the SPYSCALP.conf global configuration file."""
    
    FILENAME = "SPYSCALP.conf"
    
    @classmethod
    def initialize(cls):
        """Create config if missing, or load it."""
        path = Path(cls.FILENAME)
        if not path.exists():
            cls.save_default()
            logging.info(f"Created default configuration: {cls.FILENAME}")
            
    @classmethod
    def save_default(cls):
        """Write the default TOML structure with specific formatting."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content = [
            "SPYSCALP GLOBAL CONFIGURATION FILE",
            f"Last saved: {now} | Version: {VERSION}",
            "",
            "[tt_globals]",
            'tt-client-secret = ""',
            'tt-client-ID = ""',
            'tt-alias = ""',
            'tt-owner-name = ""'
        ]
        with open(cls.FILENAME, "w") as f:
            f.write("\n".join(content))


class DatabaseManager:
    """Manages SQLite database operations."""
    def __init__(self):
        self.connection = None
        self.current_file = None

    def open_database(self, filepath: str) -> tuple[bool, str]:
        try:
            self.close()
            path = Path(filepath).resolve()
            if not path.exists(): return False, "File not found"
            self.connection = sqlite3.connect(str(path))
            self.current_file = str(path)
            return True, f"Opened: {path.name}"
        except Exception as e:
            logging.error(f"Open DB error: {e}")
            return False, str(e)

    def save(self) -> tuple[bool, str]:
        if self.connection:
            try:
                self.connection.commit()
                return True, "Saved"
            except Exception as e: return False, str(e)
        return False, "No database open"

    def close(self):
        if self.connection:
            try:
                self.connection.commit()
                self.connection.close()
            except: pass
            self.connection = None
            self.current_file = None

    def get_tables(self) -> list[str]:
        if not self.connection: return []
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            return [row[0] for row in cursor.fetchall()]
        except: return []


class ClockWidget(Static):
    """Real-time clock widget (Time only)."""
    def on_mount(self) -> None:
        self.update_clock()
        self.set_interval(1.0, self.update_clock)
    def update_clock(self) -> None:
        self.update(datetime.now().strftime("%d %B %Y %H:%M:%S"))


class HeaderBar(Horizontal):
    """Persistent top-docked header bar with Title and Clock."""
    def compose(self) -> ComposeResult:
        yield Label("SPYSCALP", id="app-title")
        yield ClockWidget(id="app-clock")


class DBFileTree(DirectoryTree):
    """A DirectoryTree that highlights .db files."""
    def filter_paths(self, paths: list[Path]) -> list[Path]:
        return [path for path in paths if not path.name.startswith(".") and (path.is_dir() or path.suffix == ".db")]


class MainScreen(Screen):
    """The landing screen of the application."""
    def compose(self) -> ComposeResult:
        # Explicit Header for this screen
        yield HeaderBar(classes="global-header")
        with Vertical(id="main-screen-container"):
            yield Static("Welcome to SPYSCALP", classes="title")
            yield Static("Trading Application with SQLite support", classes="subtitle")
            yield Static("\n")
            yield Button("Open Database Manager", variant="primary", id="nav-to-db")
            yield Label("\nPress Q or use the Footer to exit.")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "nav-to-db":
            self.app.push_screen("database")


class DatabaseScreen(Screen):
    """The screen managing SQLite operations with integrated file browser."""
    BINDINGS = [
        Binding("F1", "stop", "STOP"),
        Binding("F2", "switch", "Switch"),
        Binding("F3", "halt", "Halt"),
        Binding("ctrl+s", "save_db", "Save"),
        Binding("escape", "back", "Back"),
    ]

    def compose(self) -> ComposeResult:
        # Explicit Duplicate Header for this screen
        yield HeaderBar(classes="global-header")
        yield Static("Database: [None] | Ready", id="db-info-bar")
        
        with Horizontal(id="main-content"):
            with Vertical(id="browser-panel"):
                yield Static("📁 File Browser (.db)", classes="panel-title")
                yield DBFileTree("./", id="file-tree")
            
            with Vertical(id="table-panel"):
                yield Static("📊 Tables", classes="panel-title")
                yield Static("(No database)", id="table-list")
            
            with Vertical(id="info-panel"):
                yield Static("⚙️ Controls", classes="panel-title")
                yield Button("Back to Main", id="nav-to-main")
                yield Static("\n[Selected Table Data]")
                yield DataTable(id="data-view")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#data-view", DataTable)
        table.add_columns("ID", "Symbol", "Qty", "Price", "Timestamp")
        table.display = False
        self.refresh_tables()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "nav-to-main": self.action_back()

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        """Handle opening a file from the tree."""
        if event.path.suffix == ".db":
            success, msg = self.app.db.open_database(str(event.path))
            self.update_status(msg)
            if success:
                self.refresh_tables()
                self.notify(f"Opened: {event.path.name}")
            else:
                self.notify(f"Failed to open database: {msg}", severity="error")

    def update_status(self, msg: str):
        try:
            status = self.query_one("#db-info-bar", Static)
            db_name = Path(self.app.db.current_file).name if self.app.db.current_file else "None"
            status.update(f"Database: [{db_name}] | {msg}")
        except Exception as e: logging.error(f"Status error: {e}")
    
    def refresh_tables(self):
        try:
            table_list = self.query_one("#table-list", Static)
            tables = self.app.db.get_tables()
            table_list.update("\n".join(f"• {t}" for t in tables) if tables else "(No tables)")
        except Exception as e: logging.error(f"Refresh error: {e}")
    
    def action_save_db(self) -> None:
        success, msg = self.app.db.save()
        self.update_status(msg); self.notify(msg if success else f"Error: {msg}")

    def action_back(self) -> None: self.app.pop_screen()


class SpyscalpApp(App):
    """Main Application managing screens and state."""
    CSS = """
    Screen { background: $surface; }
    
    .global-header {
        dock: top;
        height: 1;
        background: $primary;
        color: $text;
        text-style: bold;
        padding: 0 1;
    }
    
    #app-title { width: 1fr; }
    #app-clock { width: auto; text-align: right; }
    
    #db-info-bar {
        dock: top;
        height: 1;
        background: $secondary;
        color: $text;
        padding: 0 1;
        border-bottom: solid $primary;
    }
    
    #main-screen-container { align: center middle; height: 100%; }
    .title { text-style: bold; color: $accent; }
    .subtitle { text-style: italic; }
    
    #main-content { height: 100%; }
    
    #browser-panel {
        width: 35;
        height: 100%;
        border-right: solid $primary-darken-2;
        padding: 1;
    }
    
    #table-panel {
        width: 25;
        height: 100%;
        border-right: solid $primary-darken-2;
        padding: 1;
    }
    
    #info-panel {
        padding: 1;
        height: 100%;
    }
    
    .panel-title { text-style: bold underline; margin-bottom: 1; }
    Button { margin: 1 0; }
    """
    
    BINDINGS = [
        Binding("F1", "stop", "STOP"),
        Binding("F2", "switch", "Switch"),
        Binding("F3", "halt", "Halt"),
        Binding("q", "quit", "Quit"),
    ]
    
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        ConfigManager.initialize()
    
    def on_mount(self) -> None:
        self.install_screen(MainScreen(), name="main")
        self.install_screen(DatabaseScreen(), name="database")
        self.push_screen("main")
    
    def action_stop(self) -> None:
        self.notify("STOP command!", title="F1")
    
    def action_switch(self) -> None:
        self.notify("Switching...", title="F2")
    
    def action_halt(self) -> None:
        self.notify("TRADING HALTED!", title="F3", severity="warning")


if __name__ == "__main__":
    try:
        app = SpyscalpApp()
        app.run()
    except Exception as e:
        logging.critical(f"Global Crash: {e}", exc_info=True)