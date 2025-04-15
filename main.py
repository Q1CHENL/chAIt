import sys
import os
import json # Added json import
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLineEdit, QPushButton, QHBoxLayout, QFrame, QSizePolicy,
    QTabWidget, QInputDialog, QMessageBox, QDialog, QFormLayout, QDialogButtonBox, QLabel, QSpacerItem,
    QSystemTrayIcon, QMenu # Added QSystemTrayIcon, QMenu
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
from PyQt6.QtCore import QUrl, Qt, QStandardPaths, QDir, QSize
from PyQt6.QtGui import QIcon, QAction # Added QAction

class AddSiteDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Site")
        self.setMinimumWidth(400)
        
        # Set up the layout
        layout = QFormLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Create widgets
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter site name...")
        self.name_input.setMinimumHeight(36)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://...")
        self.url_input.setMinimumHeight(36)
        
        # Add widgets to layout
        name_label = QLabel("Name:")
        name_label.setObjectName("dialogLabel")
        url_label = QLabel("URL:")
        url_label.setObjectName("dialogLabel")
        
        layout.addRow(name_label, self.name_input)
        layout.addRow(url_label, self.url_input)
        
        # Add buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.setObjectName("dialogButtons")
        
        # Add some spacing before buttons
        layout.setVerticalSpacing(35)
        layout.addRow("", buttons)
    
    def get_inputs(self):
        return self.name_input.text().strip(), self.url_input.text().strip()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("chAIt")
        self.resize(1200, 800)

        # --- Determine Storage Location ---
        storage_location = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)
        self.persistent_dir_path = os.path.join(storage_location, "chAItProfile")
        self.sites_file_path = os.path.join(storage_location, "sites.json") # Path for sites data

        # Create the directory if it doesn't exist (for profile and sites.json)
        dir = QDir()
        if not dir.exists(storage_location): # Check parent dir first
             dir.mkpath(storage_location)
        if not dir.exists(self.persistent_dir_path):
            dir.mkpath(self.persistent_dir_path)

        # --- Load Sites ---
        self.sites = self.load_sites()

        self.web_views = {} # Dictionary to hold web views by tab index

        # --- Persistent Session Setup ---
        # Create and configure the profile
        self.profile = QWebEngineProfile("storage", self) # Give it a name and parent
        self.profile.setPersistentStoragePath(self.persistent_dir_path)
        self.profile.setCachePath(self.persistent_dir_path)
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)
        # --- End Persistent Session Setup ---

        self.init_ui()
        self.init_tray_icon() # Initialize tray icon

    def load_sites(self):
        """Loads sites from the JSON file or returns defaults."""
        default_sites = [
            {"name": "ChatGPT", "url": "https://chatgpt.com"},
            {"name": "AI Studio", "url": "https://aistudio.google.com"}
        ]
        if os.path.exists(self.sites_file_path):
            try:
                with open(self.sites_file_path, 'r') as f:
                    sites = json.load(f)
                    # Basic validation: check if it's a list of dicts with 'name' and 'url'
                    if isinstance(sites, list) and all(isinstance(s, dict) and 'name' in s and 'url' in s for s in sites):
                        print(f"Loaded {len(sites)} sites from {self.sites_file_path}")
                        return sites
                    else:
                        print(f"Warning: Invalid format in {self.sites_file_path}. Using defaults.", file=sys.stderr)
                        return default_sites
            except json.JSONDecodeError:
                print(f"Warning: Could not decode JSON from {self.sites_file_path}. Using defaults.", file=sys.stderr)
                return default_sites
            except Exception as e:
                print(f"Warning: Error loading sites file {self.sites_file_path}: {e}. Using defaults.", file=sys.stderr)
                return default_sites
        else:
            print("Sites file not found. Using default sites.")
            return default_sites

    def save_sites(self):
        """Saves the current sites list to the JSON file."""
        try:
            with open(self.sites_file_path, 'w') as f:
                json.dump(self.sites, f, indent=4)
            print(f"Saved {len(self.sites)} sites to {self.sites_file_path}")
        except Exception as e:
            print(f"Error saving sites to {self.sites_file_path}: {e}", file=sys.stderr)
            QMessageBox.warning(self, "Save Error", f"Could not save site list:\n{e}")

    def init_tray_icon(self):
        """Initializes the system tray icon and menu."""
        icon_path = os.path.join(os.path.dirname(__file__), "assets/icon.png")
        if not os.path.exists(icon_path):
            print(f"Warning: Tray icon file not found at {icon_path}", file=sys.stderr)
            # Use a default icon or handle the error appropriately
            self.tray_icon = None
            return

        self.tray_icon = QSystemTrayIcon(QIcon(icon_path), self)
        self.tray_icon.setToolTip("chAIt")

        # Create context menu
        tray_menu = QMenu()
        show_action = QAction("Show", self)
        quit_action = QAction("Quit", self)

        show_action.triggered.connect(self.show_window)
        quit_action.triggered.connect(self.close_application)

        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()

    def tray_icon_activated(self, reason):
        """Handles tray icon activation events."""
        # Show window on left click
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_window()

    def show_window(self):
        """Shows and activates the main window."""
        self.showNormal() # Restore if minimized
        self.activateWindow() # Bring to front

    def closeEvent(self, event):
        """Overrides the close event to hide the window to the tray."""
        if self.tray_icon and self.tray_icon.isVisible():
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "chAIt",
                "Application minimized to tray.",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
        else:
            # If tray icon isn't setup or visible, close normally
            event.accept()

    def close_application(self):
        """Closes the application properly."""
        if self.tray_icon:
            self.tray_icon.hide() # Hide tray icon before quitting
        QApplication.instance().quit()

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Tab Widget ---
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("tabWidget")
        self.tab_widget.setTabsClosable(False)
        self.tab_widget.setElideMode(Qt.TextElideMode.ElideNone)
        self.tab_widget.setUsesScrollButtons(False)
        # self.tab_widget.setDocumentMode(True) # Temporarily disable for debugging
        self.tab_widget.setMovable(False)

        # --- Corner Widget for Buttons ---
        corner_widget = QWidget()
        corner_layout = QHBoxLayout(corner_widget)
        # Adjust top margin to move buttons down slightly for better centering
        corner_layout.setContentsMargins(0, 3, 10, 0)  # Add 3px top margin for vertical centering
        corner_layout.setSpacing(5)
        corner_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        refresh_icon_char = "↻"
        add_icon_char = "+"

        self.refresh_btn = QPushButton(refresh_icon_char)
        self.refresh_btn.setObjectName("tabCornerBtn")
        self.refresh_btn.setFixedSize(24, 24)
        self.refresh_btn.setToolTip("Refresh Current Tab")
        self.refresh_btn.clicked.connect(self.refresh_current_tab)
        corner_layout.addWidget(self.refresh_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.add_btn = QPushButton(add_icon_char)
        self.add_btn.setObjectName("tabCornerBtn")
        self.add_btn.setFixedSize(24, 24)
        self.add_btn.setToolTip("Add New Site")
        self.add_btn.clicked.connect(self.add_site_tab)
        corner_layout.addWidget(self.add_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.tab_widget.setCornerWidget(corner_widget, Qt.Corner.TopRightCorner)

        # --- Populate Tabs ---
        while self.tab_widget.count() > 0:
            self.tab_widget.removeTab(0)
        self.web_views.clear()
        for index, site in enumerate(self.sites):
            web_view = self.create_web_view(site["url"])
            self.tab_widget.addTab(web_view, site["name"])
            self.web_views[index] = web_view
        
        # Debug: Check tab count after adding
        print(f"Tab count after adding: {self.tab_widget.count()}")

        if self.tab_widget.count() > 0:
            self.tab_widget.setCurrentIndex(0)

        main_layout.addWidget(self.tab_widget, 1)
        self.setCentralWidget(main_widget)

    def create_web_view(self, url_str):
        """Creates a QWebEngineView with the shared profile and loads the URL."""
        web_page = QWebEnginePage(self.profile, self)
        web_view = QWebEngineView()
        web_view.setPage(web_page)
        web_view.setUrl(QUrl(url_str))
        return web_view

    def refresh_current_tab(self):
        """Reloads the web view in the currently selected tab."""
        current_index = self.tab_widget.currentIndex()
        if current_index != -1:
            # Retrieve widget using the index directly from QTabWidget
            web_view = self.tab_widget.widget(current_index)
            if isinstance(web_view, QWebEngineView):
                web_view.reload()

    def add_site_tab(self):
        """Prompts user for site details, adds a new tab, and saves the updated site list."""
        dialog = AddSiteDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, url = dialog.get_inputs()

            if not name:
                QMessageBox.warning(self, "Add Site", "Site Name cannot be empty.")
                return

            if not url:
                QMessageBox.warning(self, "Add Site", "URL cannot be empty.")
                return

            # Basic URL validation
            if not url.startswith("http://") and not url.startswith("https://"):
                url = "https://" + url

            # Check for duplicates (optional but recommended)
            if any(site['name'] == name or site['url'] == url for site in self.sites):
                 QMessageBox.warning(self, "Add Site", "A site with this name or URL already exists.")
                 return

            # Add to sites list
            new_site = {"name": name, "url": url}
            self.sites.append(new_site)
            self.save_sites() # Save the updated list

            # Create and add the new tab
            web_view = self.create_web_view(url)
            new_index = self.tab_widget.addTab(web_view, name)
            # Update web_views dictionary - careful with indices if tabs can be removed
            # A more robust way might be to store web_view by name or URL if they are unique
            self.web_views[new_index] = web_view
            self.tab_widget.setCurrentIndex(new_index)

# Main entry point
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False) # Keep app running when window is hidden

    # Set Application Name and Organization - IMPORTANT for StandardPaths
    # app.setOrganizationName("chAIt") # Replace with your org name if desired
    app.setApplicationName("chAIt")

    # --- Load Stylesheet ---
    style_file_path = os.path.join(os.path.dirname(__file__), "styles/style.css")
    try:
        with open(style_file_path, "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print(f"Warning: Stylesheet file not found at {style_file_path}", file=sys.stderr)
    # --- End Load Stylesheet ---

    window = MainWindow()
    window.show()
    sys.exit(app.exec())