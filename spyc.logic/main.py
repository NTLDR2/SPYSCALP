#!/usr/bin/env python
# encoding: utf-8

import npyscreen
import sqlite3
import os


class DatabaseManager:
    """Handles SQLite database operations."""
    
    def __init__(self):
        self.connection = None
        self.current_file = None
    
    def open_database(self, filepath):
        """Open an existing SQLite database file."""
        try:
            if self.connection:
                self.close_database()
            self.connection = sqlite3.connect(filepath)
            self.current_file = filepath
            return True, f"Opened: {filepath}"
        except sqlite3.Error as e:
            return False, f"Error opening database: {e}"
    
    def create_database(self, filepath):
        """Create a new SQLite database file."""
        try:
            if self.connection:
                self.close_database()
            # Create new database file
            self.connection = sqlite3.connect(filepath)
            self.current_file = filepath
            return True, f"Created: {filepath}"
        except sqlite3.Error as e:
            return False, f"Error creating database: {e}"
    
    def save_database(self):
        """Save/commit changes to the current database."""
        if self.connection:
            try:
                self.connection.commit()
                return True, f"Saved: {self.current_file}"
            except sqlite3.Error as e:
                return False, f"Error saving database: {e}"
        return False, "No database open"
    
    def save_as_database(self, new_filepath):
        """Save the current database to a new file."""
        if not self.connection or not self.current_file:
            return False, "No database open"
        try:
            # Create a backup to the new file
            new_conn = sqlite3.connect(new_filepath)
            self.connection.backup(new_conn)
            new_conn.close()
            return True, f"Saved as: {new_filepath}"
        except sqlite3.Error as e:
            return False, f"Error saving database: {e}"
    
    def close_database(self):
        """Close the current database connection."""
        if self.connection:
            try:
                self.connection.commit()
                self.connection.close()
                self.connection = None
                self.current_file = None
                return True, "Database closed"
            except sqlite3.Error as e:
                return False, f"Error closing database: {e}"
        return True, "No database to close"
    
    def get_tables(self):
        """Get list of tables in the current database."""
        if not self.connection:
            return []
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
            return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error:
            return []
    
    def get_table_data(self, table_name):
        """Get all data from a specific table."""
        if not self.connection:
            return [], []
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"SELECT * FROM [{table_name}]")
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            return columns, rows
        except sqlite3.Error:
            return [], []
    
    def execute_query(self, query):
        """Execute a custom SQL query."""
        if not self.connection:
            return False, "No database open", []
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            if query.strip().upper().startswith("SELECT"):
                columns = [description[0] for description in cursor.description] if cursor.description else []
                rows = cursor.fetchall()
                return True, "Query executed", (columns, rows)
            else:
                self.connection.commit()
                return True, f"Query executed, {cursor.rowcount} rows affected", []
        except sqlite3.Error as e:
            return False, f"Query error: {e}", []


class MainForm(npyscreen.ActionFormWithMenus):
    """Main application form with database browser and menus."""
    
    def create(self):
        self.db_manager = self.parentApp.db_manager
        
        # Add menu
        self.menu = self.new_menu(name="File")
        self.menu.addItem("New Database", self.on_new_database, "^N")
        self.menu.addItem("Open Database", self.on_open_database, "^O")
        self.menu.addItem("Save", self.on_save_database, "^S")
        self.menu.addItem("Save As...", self.on_save_as_database)
        self.menu.addItem("Close Database", self.on_close_database, "^W")
        self.menu.addItem("Exit", self.on_exit, "^Q")
        
        # Status display
        self.status = self.add(npyscreen.TitleText, name="Status:", value="No database open", editable=False)
        
        # File path input for opening/creating databases
        self.filepath = self.add(npyscreen.TitleFilenameCombo, name="Database File:")
        
        # Table list
        self.add(npyscreen.FixedText, value="Tables:", editable=False)
        self.table_list = self.add(npyscreen.SelectOne, max_height=6, values=[], scroll_exit=True)
        self.table_list.when_value_edited = self.on_table_selected
        
        # Data display
        self.add(npyscreen.FixedText, value="Table Data:", editable=False)
        self.data_display = self.add(npyscreen.MultiLineEdit, max_height=8, editable=False)
        
        # SQL Query input
        self.query_input = self.add(npyscreen.TitleText, name="SQL Query:")
        
        # Query result
        self.query_result = self.add(npyscreen.MultiLineEdit, max_height=-2, editable=False, 
                                      value="Enter a SQL query and press OK to execute")
    
    def on_new_database(self):
        """Create a new database file."""
        filepath = self.filepath.value
        if filepath:
            if not filepath.endswith('.db') and not filepath.endswith('.sqlite'):
                filepath += '.db'
            success, message = self.db_manager.create_database(filepath)
            self.status.value = message
            if success:
                self.refresh_tables()
            self.display()
        else:
            self.status.value = "Please enter a filename"
            self.display()
    
    def on_open_database(self):
        """Open an existing database file."""
        filepath = self.filepath.value
        if filepath and os.path.exists(filepath):
            success, message = self.db_manager.open_database(filepath)
            self.status.value = message
            if success:
                self.refresh_tables()
            self.display()
        else:
            self.status.value = "File not found or no file specified"
            self.display()
    
    def on_save_database(self):
        """Save the current database."""
        success, message = self.db_manager.save_database()
        self.status.value = message
        self.display()
    
    def on_save_as_database(self):
        """Save database to a new file."""
        filepath = self.filepath.value
        if filepath:
            if not filepath.endswith('.db') and not filepath.endswith('.sqlite'):
                filepath += '.db'
            success, message = self.db_manager.save_as_database(filepath)
            self.status.value = message
            self.display()
        else:
            self.status.value = "Please enter a filename for Save As"
            self.display()
    
    def on_close_database(self):
        """Close the current database."""
        success, message = self.db_manager.close_database()
        self.status.value = message
        self.table_list.values = []
        self.data_display.value = ""
        self.display()
    
    def on_exit(self):
        """Exit the application."""
        self.db_manager.close_database()
        self.parentApp.switchForm(None)
    
    def refresh_tables(self):
        """Refresh the list of tables."""
        tables = self.db_manager.get_tables()
        self.table_list.values = tables
        self.table_list.value = None
        self.data_display.value = ""
    
    def on_table_selected(self):
        """Handle table selection to display data."""
        if self.table_list.value is not None and len(self.table_list.values) > 0:
            selected_idx = self.table_list.value[0] if isinstance(self.table_list.value, list) else self.table_list.value
            if 0 <= selected_idx < len(self.table_list.values):
                table_name = self.table_list.values[selected_idx]
                columns, rows = self.db_manager.get_table_data(table_name)
                if columns:
                    # Format data for display
                    header = " | ".join(columns)
                    separator = "-" * len(header)
                    data_lines = [header, separator]
                    for row in rows[:50]:  # Limit to first 50 rows for display
                        data_lines.append(" | ".join(str(cell) for cell in row))
                    if len(rows) > 50:
                        data_lines.append(f"... and {len(rows) - 50} more rows")
                    self.data_display.value = "\n".join(data_lines)
                else:
                    self.data_display.value = "No data or error reading table"
    
    def on_ok(self):
        """Execute SQL query when OK is pressed."""
        query = self.query_input.value
        if query:
            success, message, result = self.db_manager.execute_query(query)
            if success and result:
                columns, rows = result
                if columns:
                    header = " | ".join(columns)
                    separator = "-" * len(header)
                    data_lines = [message, "", header, separator]
                    for row in rows[:100]:
                        data_lines.append(" | ".join(str(cell) for cell in row))
                    if len(rows) > 100:
                        data_lines.append(f"... and {len(rows) - 100} more rows")
                    self.query_result.value = "\n".join(data_lines)
                else:
                    self.query_result.value = message
            else:
                self.query_result.value = message
            self.refresh_tables()  # Refresh in case tables were modified
            self.display()
    
    def on_cancel(self):
        """Exit on cancel."""
        self.on_exit()


class SQLiteBrowserApp(npyscreen.NPSAppManaged):
    """Main application class for SQLite Browser."""
    
    def onStart(self):
        self.db_manager = DatabaseManager()
        self.addForm("MAIN", MainForm, name="SQLite Database Browser - Press Ctrl+X for Menu")


if __name__ == "__main__":
    App = SQLiteBrowserApp()
    App.run()
