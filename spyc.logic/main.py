#!/usr/bin/env python
# encoding: utf-8
"""
SPYSCALP - Trading Interface with SQLite Support
Built with Textual for reliable real-time updates
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from textual.app import App, ComposeResult
from textual.widgets import Footer, Static, Input, Button, DataTable
from textual.containers import Container, Horizontal, Vertical
from textual.binding import Binding
from textual.screen import ModalScreen

# Setup logging to file to catch crashes
logging.basicConfig(
    filename='spyscalp_debug.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class DatabaseManager:
    """Manages SQLite database operations."""
    
    def __init__(self):
        self.connection = None
        self.current_file = None
    
    def new_database(self, filepath: str) -> tuple[bool, str]:
        """Create a new SQLite database."""
        try:
            logging.info(f"Creating new database: {filepath}")
            self.close()
            path = Path(filepath)
            if not path.suffix:
                path = path.with_suffix('.db')
            
            # Ensure directory exists
            path.parent.mkdir(parents=True, exist_ok=True)
            
            self.connection = sqlite3.connect(str(path))
            self.current_file = str(path)
            cursor = self.connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY,
                    symbol TEXT,
                    quantity INTEGER,
                    price REAL,
                    timestamp TEXT
                )
            """)
            self.connection.commit()
            logging.info("Database created successfully")
            return True, f"Created: {path.name}"
        except Exception as e:
            logging.error(f"Error creating database: {e}")
            return False, str(e)
    
    def open_database(self, filepath: str) -> tuple[bool, str]:
        """Open an existing database."""
        try:
            logging.info(f"Opening database: {filepath}")
            self.close()
            path = Path(filepath).resolve()
            if not path.exists():
                return False, "File not found"
            self.connection = sqlite3.connect(str(path))
            self.current_file = str(path)
            logging.info("Database opened successfully")
            return True, f"Opened: {path.name}"
        except Exception as e:
            logging.error(f"Error opening database: {e}")
            return False, str(e)
    
    def save(self) -> tuple[bool, str]:
        """Save (commit) the current database."""
        if self.connection:
            try:
                self.connection.commit()
                return True, "Saved"
            except Exception as e:
                return False, str(e)
        return False, "No database open"
    
    def close(self):
        """Close the current database."""
        if self.connection:
            try:
                self.connection.commit()
                self.connection.close()
            except Exception as e:
                logging.warning(f"Error closing database: {e}")
            self.connection = None
            self.current_file = None
    
    def get_tables(self) -> list[str]:
        """Get list of tables."""
        if not self.connection:
            return []
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Error fetching tables: {e}")
            return []


class FileInputScreen(ModalScreen[str]):
    """Modal screen for file path input using Textual's built-in dismiss mechanism."""
    
    CSS = """
    FileInputScreen {
        align: center middle;
    }
    
    #dialog-box {
        width: 60;
        height: 11;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    
    #dialog-title {
        text-style: bold;
        margin-bottom: 1;
    }
    
    #button-row {
        margin-top: 1;
    }
    
    Button {
        margin-right: 2;
    }
    """
    
    def __init__(self, title: str, default: str = ""):
        super().__init__()
        self.title_text = title
        self.default = default
    
    def compose(self) -> ComposeResult:
        with Container(id="dialog-box"):
            yield Static(self.title_text, id="dialog-title")
            yield Input(value=self.default, placeholder="Enter file path...", id="file-input")
            with Horizontal(id="button-row"):
                yield Button("OK", variant="primary", id="ok-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok-btn":
            input_widget = self.query_one("#file-input", Input)
            self.dismiss(input_widget.value)
        else:
            self.dismiss(None)
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value)


class ClockWidget(Static):
    """Real-time clock widget."""
    
    def on_mount(self) -> None:
        self.update_clock()
        self.set_interval(1.0, self.update_clock)
    
    def update_clock(self) -> None:
        now = datetime.now()
        clock_text = now.strftime("%d %B %Y %H:%M:%S")
        self.update(f"SPYSCALP{' ' * 20}{clock_text}")


class SpyscalpApp(App):
    """SPYSCALP Trading Application with SQLite support."""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #header-bar {
        dock: top;
        height: 1;
        background: $primary;
        color: $text;
        text-style: bold;
    }
    
    #status-bar {
        dock: top;
        height: 1;
        background: $secondary;
        color: $text;
    }
    
    #main-content {
        height: 100%;
        padding: 1;
    }
    
    #table-panel {
        width: 25;
        height: 100%;
        border: solid $primary;
        padding: 1;
    }
    
    #data-panel {
        height: 100%;
        padding: 1;
    }
    
    .panel-title {
        text-style: bold underline;
        margin-bottom: 1;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+n", "new_db", "New DB"),
        Binding("ctrl+o", "open_db", "Open DB"),
        Binding("ctrl+s", "save_db", "Save"),
        Binding("f1", "stop", "STOP"),
        Binding("f2", "switch", "Switch"),
        Binding("f3", "halt", "Halt"),
        Binding("q", "quit", "Quit"),
    ]
    
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
    
    def compose(self) -> ComposeResult:
        yield ClockWidget(id="header-bar")
        yield Static("Database: [None] | Ready", id="status-bar")
        with Horizontal(id="main-content"):
            with Vertical(id="table-panel"):
                yield Static("Tables", classes="panel-title")
                yield Static("(No database)", id="table-list")
            with Vertical(id="data-panel"):
                yield Static("SPYSCALP Trading System", classes="panel-title")
                yield Static("Press Ctrl+N to create a new database")
                yield Static("Press Ctrl+O to open an existing database")
                yield DataTable(id="data-view")
        yield Footer()
    
    def on_mount(self) -> None:
        table = self.query_one("#data-view", DataTable)
        table.add_columns("ID", "Symbol", "Qty", "Price", "Timestamp")
        table.display = False # Hide until needed
    
    def update_status(self, msg: str):
        """Update the status bar."""
        try:
            status = self.query_one("#status-bar", Static)
            db_name = Path(self.db.current_file).name if self.db.current_file else "None"
            status.update(f"Database: [{db_name}] | {msg}")
        except Exception as e:
            logging.error(f"Status update error: {e}")
    
    def refresh_tables(self):
        """Refresh the table list."""
        try:
            table_list = self.query_one("#table-list", Static)
            tables = self.db.get_tables()
            if tables:
                table_list.update("\n".join(f"• {t}" for t in tables))
            else:
                table_list.update("(No tables)")
        except Exception as e:
            logging.error(f"Refresh tables error: {e}")
    
    def action_new_db(self) -> None:
        """Create new database."""
        def handle_new_db(filepath: str | None) -> None:
            if not filepath:
                return
            try:
                success, msg = self.db.new_database(filepath)
                self.update_status(msg)
                if success:
                    self.refresh_tables()
                    self.notify(f"Created: {filepath}")
                else:
                    self.notify(f"Error: {msg}", severity="error")
            except Exception as e:
                logging.error(f"Callback error (New DB): {e}")
                self.notify("An internal error occurred", severity="error")
        
        self.push_screen(FileInputScreen("New Database", "spyscalp.db"), handle_new_db)
    
    def action_open_db(self) -> None:
        """Open existing database."""
        def handle_open_db(filepath: str | None) -> None:
            if not filepath:
                return
            try:
                success, msg = self.db.open_database(filepath)
                self.update_status(msg)
                if success:
                    self.refresh_tables()
                    self.notify(f"Opened: {filepath}")
                else:
                    self.notify(f"Error: {msg}", severity="error")
            except Exception as e:
                logging.error(f"Callback error (Open DB): {e}")
                self.notify("An internal error occurred", severity="error")
        
        self.push_screen(FileInputScreen("Open Database", ""), handle_open_db)
    
    def action_save_db(self) -> None:
        """Save database."""
        success, msg = self.db.save()
        self.update_status(msg)
        self.notify(msg if success else f"Error: {msg}")
    
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