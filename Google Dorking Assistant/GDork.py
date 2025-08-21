import sys
import webbrowser
import re
import json
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QLabel, QLineEdit, QComboBox, QTextEdit,
    QPushButton, QTabWidget, QListWidget, QMessageBox, QScrollArea,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QStatusBar, QMainWindow,
    QMenu, QTreeWidgetItemIterator, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction

class GoogleDorkApp(QMainWindow):
    """
    a desktop app for making google dork queries, using pyqt6
    """
    # where we save the history
    HISTORY_FILE = "history.json"

    def __init__(self):
        super().__init__()
        self.setup_the_window()
        self.load_history()

    def setup_the_window(self):
        """sets up the main window and all the bits inside"""
        self.setWindowTitle("Google Dorking Assistant")
        self.setGeometry(100, 100, 1000, 800)
        self.setMinimumSize(850, 700)

        # the main widget that holds everything
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        big_layout = QVBoxLayout(main_widget)

        # this is for the tabs
        self.tabs = QTabWidget()
        big_layout.addWidget(self.tabs)

        # making the actual tabs now
        builder_tab = QWidget()
        history_tab = QWidget()

        self.tabs.addTab(builder_tab, "Query Builder")
        self.tabs.addTab(history_tab, "Query History")

        # a place to keep all our input boxes
        self.widgets = {}

        # putting stuff in the tabs
        self.make_the_builder_tab(builder_tab)
        self.make_the_history_tab(history_tab)

        # the little status bar at the bottom
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready", 3000)

        # connect the input boxes so they update the preview automatically
        for widget in self.widgets.values():
            if isinstance(widget, QLineEdit):
                widget.textChanged.connect(self.update_preview)
            elif isinstance(widget, QComboBox):
                widget.currentTextChanged.connect(self.update_preview)

        self.update_preview()
        self.make_it_look_nice()

    def make_the_builder_tab(self, parent_tab):
        """builds the main tab where you create the queries"""
        layout_for_tab = QVBoxLayout(parent_tab)
        
        # the box for the main search words
        box1 = QGroupBox("Core Search Terms (use comma for OR, e.g., admin, user)")
        box1_layout = QGridLayout(box1)
        
        self.widgets['keywords'] = QLineEdit()
        self.widgets['keywords'].setPlaceholderText("e.g., confidential data, internal report")
        
        self.widgets['exclude_keywords'] = QLineEdit()
        self.widgets['exclude_keywords'].setPlaceholderText("e.g., public, template, sample")

        box1_layout.addWidget(QLabel("Keywords:"), 0, 0)
        box1_layout.addWidget(self.widgets['keywords'], 0, 1)
        box1_layout.addWidget(QLabel("Exclude Keywords (-):"), 1, 0)
        box1_layout.addWidget(self.widgets['exclude_keywords'], 1, 1)
        layout_for_tab.addWidget(box1)

        # the box for all the special google operators
        box2 = QGroupBox("Google Dork Operators (use comma for OR)")
        box2_layout = QGridLayout(box2)

        # adding all the operator input fields
        self.add_an_operator(box2_layout, 0, "Site", "example.com", "Search within a specific website.")
        self.add_an_operator(box2_layout, 1, "In Title", "index of, login", "Search for terms in the page title.")
        self.add_an_operator(box2_layout, 2, "In URL", "admin.php, login.jsp", "Search for terms in the page URL.")
        self.add_an_operator(box2_layout, 3, "In Text", "password, secret", "Search for terms in the body of the page.")
        self.add_an_operator(box2_layout, 4, "Related", "google.com", "Find sites related to a given domain.")
        self.add_an_operator(box2_layout, 5, "Cache", "example.com", "Find the cached version of a page.")
        
        # the dropdown for file types
        self.widgets['filetype'] = QComboBox()
        filetypes = ["", "pdf", "docx", "xlsx", "pptx", "txt", "log", "php", "asp", "sql", "env", "conf", "config", "bak", "ini", "pem", "crt"]
        self.widgets['filetype'].addItems(filetypes)
        box2_layout.addWidget(QLabel("filetype:"), 6, 0)
        box2_layout.addWidget(self.widgets['filetype'], 6, 1)
        
        layout_for_tab.addWidget(box2)

        # the preview box and action buttons
        self.make_the_preview_box(layout_for_tab)
        self.make_the_bottom_buttons(layout_for_tab)
        layout_for_tab.addStretch()

    def add_an_operator(self, the_grid, row, name, placeholder, tooltip_text):
        """a little helper to make the operator input boxes"""
        key = name.lower().replace(' ', '_')
        prefix = f"{name.lower().replace(' ', '')}:"
        label = QLabel(prefix)
        input_box = QLineEdit()
        input_box.setPlaceholderText(placeholder)
        input_box.setToolTip(tooltip_text)
        the_grid.addWidget(label, row, 0)
        the_grid.addWidget(input_box, row, 1)
        self.widgets[key] = input_box

    def make_the_history_tab(self, parent_tab):
        """builds the history tab"""
        layout = QVBoxLayout(parent_tab)
        history_box = QGroupBox("Saved Queries")
        history_box_layout = QHBoxLayout(history_box)
        layout.addWidget(history_box)

        left_side = QVBoxLayout()
        search_bar = QLineEdit()
        search_bar.setPlaceholderText("Search history...")
        search_bar.textChanged.connect(self.filter_history)
        left_side.addWidget(search_bar)

        self.history_listbox = QListWidget()
        self.history_listbox.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.history_listbox.customContextMenuRequested.connect(self.right_click_history_menu)
        left_side.addWidget(self.history_listbox)
        history_box_layout.addLayout(left_side, 1)

        right_side_buttons = QVBoxLayout()
        history_box_layout.addLayout(right_side_buttons)
        
        btn_load = QPushButton(" Load Selected")
        btn_load.clicked.connect(self.load_from_history)
        right_side_buttons.addWidget(btn_load)
        
        btn_delete = QPushButton(" Delete Selected")
        btn_delete.clicked.connect(self.delete_from_history)
        right_side_buttons.addWidget(btn_delete)

        btn_export = QPushButton(" Export to TXT")
        btn_export.clicked.connect(self.save_history_as_txt)
        right_side_buttons.addWidget(btn_export)

        right_side_buttons.addStretch()

    def make_the_preview_box(self, parent_layout):
        """makes the box that shows the final query"""
        preview_box = QGroupBox("Generated Query Preview")
        preview_box_layout = QVBoxLayout(preview_box)
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setFixedHeight(120)
        self.preview_text.setObjectName("PreviewText")
        preview_box_layout.addWidget(self.preview_text)
        parent_layout.addWidget(preview_box)

    def make_the_bottom_buttons(self, parent_layout):
        """makes the main buttons like copy, search, etc."""
        buttons_layout = QHBoxLayout()
        btn_clear = QPushButton("Clear All")
        btn_clear.clicked.connect(self.clear_all_fields)
        buttons_layout.addWidget(btn_clear)
        buttons_layout.addStretch()
        btn_copy = QPushButton("Copy to Clipboard")
        btn_copy.clicked.connect(self.copy_to_clipboard)
        buttons_layout.addWidget(btn_copy)
        btn_search = QPushButton("Search in Browser")
        btn_search.clicked.connect(self.search_in_browser)
        buttons_layout.addWidget(btn_search)
        btn_save = QPushButton("Save to History")
        btn_save.clicked.connect(self.save_to_history)
        parent_layout.addLayout(buttons_layout)

    def handle_or_and_quotes(self, text, operator=""):
        """handles the comma for 'OR' and adds quotes"""
        if not text:
            return ""
        
        bits = [part.strip() for part in text.split(',')]
        finished_bits = []
        for part in bits:
            # if there's a space, it needs quotes
            if ' ' in part and not (part.startswith('"') and part.endswith('"')):
                part = f'"{part}"'
            
            if operator:
                finished_bits.append(f"{operator}:{part}")
            else:
                finished_bits.append(part)
        
        # if there are multiple parts, wrap them in ( ... OR ... )
        if len(finished_bits) > 1:
            return f"({ ' OR '.join(finished_bits) })"
        return finished_bits[0]

    def put_the_query_together(self, parts):
        """builds the final query string from all the pieces"""
        all_the_parts = []
        
        if parts.get("keywords"):
            all_the_parts.append(self.handle_or_and_quotes(parts["keywords"]))

        for key, value in parts.items():
            if key in ["keywords", "exclude_keywords"] or not value:
                continue
            operator = key.replace('_', '')
            all_the_parts.append(self.handle_or_and_quotes(value, operator))

        if parts.get("exclude_keywords"):
            excluded_words = [part.strip() for part in parts["exclude_keywords"].split(',')]
            for word in excluded_words:
                if ' ' in word:
                    all_the_parts.append(f'-\"{word}\"')
                else:
                    all_the_parts.append(f'-{word}')

        return " ".join(filter(None, all_the_parts))

    def update_preview(self, *args):
        """updates the preview box whenever you type something"""
        parts = self.get_all_user_input()
        the_final_query = self.put_the_query_together(parts)
        self.preview_text.setText(the_final_query)
    
    def get_all_user_input(self):
        """gets all the text from the input boxes"""
        all_the_text = {}
        for key, widget in self.widgets.items():
            value = ""
            if isinstance(widget, QLineEdit):
                value = widget.text().strip()
            elif isinstance(widget, QComboBox):
                value = widget.currentText()
            all_the_text[key] = value
        return all_the_text

    def copy_to_clipboard(self):
        """copies the query to the clipboard"""
        query = self.preview_text.toPlainText().strip()
        if query:
            QApplication.clipboard().setText(query)
            self.statusBar.showMessage("Query copied to clipboard!", 3000)
        else:
            QMessageBox.warning(self, "Warning", "Query is empty, nothing to copy.")

    def search_in_browser(self):
        """opens the query in your web browser"""
        query = self.preview_text.toPlainText().strip()
        if query:
            url = f"https://www.google.com/search?q={query}"
            webbrowser.open(url)
            self.statusBar.showMessage(f"Searching for: {query}", 3000)
        else:
            QMessageBox.warning(self, "Warning", "Query is empty, nothing to search.")

    def clear_all_fields(self):
        """clears all the input boxes"""
        for widget in self.widgets.values():
            if isinstance(widget, QLineEdit):
                widget.clear()
            elif isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)
        self.update_preview()
        self.statusBar.showMessage("All fields cleared.", 3000)

    def save_to_history(self):
        """saves the current query to the history list"""
        query_parts = self.get_all_user_input()
        query_string = self.put_the_query_together(query_parts)
        if not any(query_parts.values()):
            QMessageBox.warning(self, "Warning", "Cannot save an empty query.")
            return
        # check if it's already saved
        for i in range(self.history_listbox.count()):
            item = self.history_listbox.item(i)
            if item.text() == query_string:
                QMessageBox.information(self, "Info", "This query is already in your history.")
                return
        item = QListWidgetItem(query_string)
        item.setData(Qt.ItemDataRole.UserRole, query_parts)
        self.history_listbox.addItem(item)
        self.save_history()
        self.statusBar.showMessage("Query saved to history.", 3000)

    def load_from_history(self):
        """loads a selected query from the history list"""
        selected_items = self.history_listbox.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select a query from the history to load.")
            return
        
        # if you select a bunch of things, just load the first one
        self.load_one_history_item(selected_items[0])

    def delete_from_history(self):
        """deletes the selected query from the history list"""
        selected_items = self.history_listbox.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select a query to delete.")
            return
        for item in selected_items:
            self.history_listbox.takeItem(self.history_listbox.row(item))
        self.save_history()
        self.statusBar.showMessage(f"Deleted {len(selected_items)} item(s) from history.", 3000)

    def save_history(self):
        """saves the whole history list to a json file"""
        stuff_to_save = []
        for i in range(self.history_listbox.count()):
            item = self.history_listbox.item(i)
            stuff_to_save.append({
                "display_text": item.text(),
                "query_parts": item.data(Qt.ItemDataRole.UserRole)
            })
        try:
            with open(self.HISTORY_FILE, "w") as f:
                json.dump(stuff_to_save, f, indent=4)
        except IOError as e:
            QMessageBox.critical(self, "Error", f"Could not save history file: {e}")

    def load_history(self):
        """loads the history from the json file when the app starts"""
        if not os.path.exists(self.HISTORY_FILE):
            return
        try:
            with open(self.HISTORY_FILE, "r") as f:
                stuff_from_file = json.load(f)
            for entry in stuff_from_file:
                item = QListWidgetItem(entry["display_text"])
                item.setData(Qt.ItemDataRole.UserRole, entry["query_parts"])
                self.history_listbox.addItem(item)
        except (IOError, json.JSONDecodeError) as e:
            QMessageBox.critical(self, "Error", f"Could not load history file: {e}")

    def fill_in_the_boxes(self, saved_parts):
        """fills in the input boxes from a saved query"""
        self.clear_all_fields()
        for key, value in saved_parts.items():
            if key in self.widgets:
                widget = self.widgets[key]
                if isinstance(widget, QLineEdit):
                    widget.setText(value)
                elif isinstance(widget, QComboBox):
                    index = widget.findText(value, Qt.MatchFlag.MatchFixedString)
                    if index >= 0:
                        widget.setCurrentIndex(index)
        self.update_preview()

    def filter_history(self, search_text):
        """filters the history list as you type in the search bar"""
        for i in range(self.history_listbox.count()):
            item = self.history_listbox.item(i)
            item.setHidden(search_text.lower() not in item.text().lower())

    def right_click_history_menu(self, position):
        """the right-click menu for the history list"""
        item = self.history_listbox.itemAt(position)
        if not item: return
        
        menu = QMenu()
        load_action = QAction("Load Query", self)
        load_action.triggered.connect(lambda: self.load_one_history_item(item))
        delete_action = QAction("Delete Query", self)
        delete_action.triggered.connect(lambda: self.delete_one_history_item(item))
        
        menu.addAction(load_action)
        menu.addAction(delete_action)
        menu.exec(self.history_listbox.mapToGlobal(position))
        
    def load_one_history_item(self, the_item):
        """loads a specific item from the history list"""
        query_parts = the_item.data(Qt.ItemDataRole.UserRole)
        self.fill_in_the_boxes(query_parts)
        self.statusBar.showMessage("Loaded query from history.", 3000)

    def delete_one_history_item(self, the_item):
        """deletes a specific item from the history list"""
        self.history_listbox.takeItem(self.history_listbox.row(the_item))
        self.save_history()
        self.statusBar.showMessage("Deleted query from history.", 3000)

    def save_history_as_txt(self):
        """saves the history list to a plain text file"""
        if self.history_listbox.count() == 0:
            QMessageBox.warning(self, "Warning", "History is empty. Nothing to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Save History As", "dork_history.txt", "Text Files (*.txt)")

        if file_path:
            try:
                with open(file_path, 'w') as f:
                    for i in range(self.history_listbox.count()):
                        f.write(self.history_listbox.item(i).text() + '\n')
                self.statusBar.showMessage(f"History successfully exported to {file_path}", 5000)
            except IOError as e:
                QMessageBox.critical(self, "Error", f"Could not save file: {e}")

    def make_it_look_nice(self):
        """applies a clean, light style to the app"""
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #f0f0f0;
                color: #333;
                font-family: Segoe UI, Arial, sans-serif;
                font-size: 10pt;
            }
            QTabWidget::pane {
                border-top: 2px solid #ccc;
            }
            QTabBar::tab {
                background: #e1e1e1;
                color: #333;
                padding: 8px 20px;
                border: 1px solid #ccc;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #f0f0f0;
                font-weight: bold;
                border-bottom: 1px solid #f0f0f0;
            }
            QGroupBox {
                background-color: #fafafa;
                border: 1px solid #ccc;
                border-radius: 4px;
                margin-top: 1em;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QLineEdit, QComboBox, QTextEdit, QListWidget, QTreeWidget {
                background-color: #fff;
                border: 1px solid #ccc;
                padding: 5px;
                border-radius: 3px;
            }
            QTextEdit#PreviewText {
                font-family: Consolas, Courier, monospace;
                background-color: #e9e9e9;
            }
            QPushButton {
                background-color: #e1e1e1;
                border: 1px solid #ccc;
                padding: 6px 12px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #cacaca;
                border: 1px solid #adadad;
            }
            QPushButton:pressed {
                background-color: #b0b0b0;
            }
            QStatusBar {
                background-color: #e1e1e1;
            }
        """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = GoogleDorkApp()
    ex.show()
    sys.exit(app.exec())
