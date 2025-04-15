import os
import sys
import json
import importlib.resources
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QTabWidget,
    QMessageBox, QSystemTrayIcon, QMenu, QApplication
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
from PyQt6.QtCore import QUrl, Qt, QStandardPaths, QDir
from PyQt6.QtGui import QIcon, QAction

from .dialogs import AddSiteDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("chAIt")
        self.resize(1200, 800)

        storage_location = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)
        app_name = QApplication.applicationName() if QApplication.applicationName() else "chAIt"
        self.persistent_dir_path = os.path.join(storage_location, f"{app_name}Profile")
        self.sites_file_path = os.path.join(storage_location, "sites.json")

        dir = QDir()
        if not dir.exists(storage_location):
             dir.mkpath(storage_location)
        if not dir.exists(self.persistent_dir_path):
            dir.mkpath(self.persistent_dir_path)

        self.sites = self.load_sites()

        self.web_views = {} # Dictionary to hold web views by tab index

        self.profile = QWebEngineProfile("storage", self)
        self.profile.setPersistentStoragePath(self.persistent_dir_path)
        self.profile.setCachePath(self.persistent_dir_path)
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)

        self.init_ui()
        self.init_tray_icon()

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
        try:
            icon_ref = importlib.resources.files('chait').joinpath('assets/icon.png')
            with importlib.resources.as_file(icon_ref) as icon_path:
                 if (icon_path.is_file()):
                     self.tray_icon = QSystemTrayIcon(QIcon(str(icon_path)), self)
                     self.tray_icon.setToolTip("chAIt")
                 else:
                     print(f"Warning: Tray icon resource path is not a file: {icon_path}", file=sys.stderr)
                     self.tray_icon = None
                     return
        except ModuleNotFoundError:
             print("Error: Could not find the 'chait' package to load tray icon resource from.", file=sys.stderr)
             self.tray_icon = None
             return
        except FileNotFoundError:
             print("Error: Tray icon resource 'assets/icon.png' not found within the 'chait' package.", file=sys.stderr)
             self.tray_icon = None
             return
        except Exception as e:
             print(f"Warning: Could not load tray icon resource: {e}", file=sys.stderr)
             self.tray_icon = None
             return

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
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_window()

    def show_window(self):
        """Shows and activates the main window."""
        self.showNormal()
        self.activateWindow()

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
            event.accept()

    def close_application(self):
        """Closes the application properly."""
        if self.tray_icon:
            self.tray_icon.hide()
        QApplication.instance().quit()

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("tabWidget")
        self.tab_widget.setTabsClosable(False)
        self.tab_widget.setElideMode(Qt.TextElideMode.ElideNone)
        self.tab_widget.setUsesScrollButtons(False)
        self.tab_widget.setMovable(False)

        corner_widget = QWidget()
        corner_layout = QHBoxLayout(corner_widget)
        corner_layout.setContentsMargins(0, 3, 10, 0)
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

        while self.tab_widget.count() > 0:
            self.tab_widget.removeTab(0)
        self.web_views.clear()
        for index, site in enumerate(self.sites):
            web_view = self.create_web_view(site["url"])
            self.tab_widget.addTab(web_view, site["name"])
            self.web_views[index] = web_view

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
            web_view = self.tab_widget.widget(current_index)
            if isinstance(web_view, QWebEngineView):
                web_view.reload()

    def add_site_tab(self):
        """Prompts user for site details, adds a new tab, and saves the updated site list."""
        dialog = AddSiteDialog(self)
        if dialog.exec() == AddSiteDialog.DialogCode.Accepted:
            name, url = dialog.get_inputs()

            if not name:
                QMessageBox.warning(self, "Add Site", "Site Name cannot be empty.")
                return

            if not url:
                QMessageBox.warning(self, "Add Site", "URL cannot be empty.")
                return

            if not url.startswith("http://") and not url.startswith("https://"):
                url = "https://" + url

            if any(site['name'] == name or site['url'] == url for site in self.sites):
                 QMessageBox.warning(self, "Add Site", "A site with this name or URL already exists.")
                 return

            new_site = {"name": name, "url": url}
            self.sites.append(new_site)
            self.save_sites()

            web_view = self.create_web_view(url)
            new_index = self.tab_widget.addTab(web_view, name)
            self.web_views[new_index] = web_view
            self.tab_widget.setCurrentIndex(new_index)
