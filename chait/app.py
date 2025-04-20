import os
import sys
import json
import importlib.resources
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QTabWidget,
    QMessageBox, QSystemTrayIcon, QMenu, QApplication, QLineEdit, QLabel, QDialog
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
from PyQt6.QtCore import QUrl, Qt, QStandardPaths, QDir
from PyQt6.QtGui import QIcon, QAction, QKeySequence, QShortcut

from .dialogs import AddSiteDialog, ConfirmDialog

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
        # Ctrl+F shows find bar, Esc hides
        self.find_sc = QShortcut(QKeySequence("Ctrl+F"), self)
        self.find_sc.activated.connect(self.find_in_page)
        self.close_find_sc = QShortcut(QKeySequence("Esc"), self)
        self.close_find_sc.activated.connect(self.hide_find_bar)
        self.init_tray_icon()

        # initialize search state
        self.search_text = ""
        self.search_count = 0
        self.search_index = 0

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
        corner_layout.setContentsMargins(0, 3, 10, 3)
        corner_layout.setSpacing(5)
        corner_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        refresh_icon_char = "⟳"
        add_icon_char = "+"

        self.refresh_btn = QPushButton(refresh_icon_char)
        self.refresh_btn.setObjectName("tabCornerBtn")
        self.refresh_btn.setFixedSize(24, 24)
        self.refresh_btn.setToolTip("Refresh Current Tab")
        self.refresh_btn.clicked.connect(self.refresh_current_tab)

        self.refresh_sc = QShortcut(QKeySequence("Ctrl+R"), self)
        self.refresh_sc.activated.connect(self.refresh_current_tab)
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
        # right-click context menu on tabs
        self.tab_widget.tabBar().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tab_widget.tabBar().customContextMenuRequested.connect(self.on_tab_context_menu)

        # find bar widget for real-time search
        self.find_bar = QWidget()
        find_layout = QHBoxLayout(self.find_bar)
        find_layout.setContentsMargins(5,2,5,2)
        find_layout.setSpacing(5)
        # label shows current/total matches
        self.find_label = QLabel("0/0")
        self.find_input = QLineEdit()
        # always show border, styled differently when focused
        self.find_input.setFrame(True)
        self.find_input.setStyleSheet(
            # normal: 1px border + 2px padding, focus: 2px border + 1px padding to keep content area same
            "QLineEdit{border:1px solid #ccc;border-radius:4px;padding:2px;} "
            "QLineEdit:focus{border:2px solid #007acc;border-radius:4px;padding:1px;}"
        )
        self.find_input.setPlaceholderText("Search...")
        # buttons to navigate matches
        self.prev_find_btn = QPushButton("▲")
        self.prev_find_btn.setFixedSize(24, 24)
        self.prev_find_btn.setToolTip("Previous Match")
        self.prev_find_btn.clicked.connect(self.find_prev)
        self.next_find_btn = QPushButton("▼")
        self.next_find_btn.setFixedSize(24, 24)
        self.next_find_btn.setToolTip("Next Match")
        self.next_find_btn.clicked.connect(self.find_next)
        # frameless until hover: flat buttons with hover border
        self.prev_find_btn.setFlat(True)
        self.next_find_btn.setFlat(True)
        btn_style = '''
            QPushButton { border: none; background: transparent; }
            QPushButton:hover { border: 1px solid #007acc; border-radius:4px; background: rgba(0,122,204,0.1); }
        '''
        self.prev_find_btn.setStyleSheet(btn_style)
        self.next_find_btn.setStyleSheet(btn_style)
        find_layout.addWidget(self.find_label)
        find_layout.addWidget(self.prev_find_btn)
        find_layout.addWidget(self.next_find_btn)
        find_layout.addWidget(self.find_input, 1)
        main_layout.addWidget(self.find_bar)
        self.find_bar.hide()
        # connect real-time find
        self.find_input.textChanged.connect(self.do_find)
        self.find_input.returnPressed.connect(self.find_next)
        self.setCentralWidget(main_widget)

    def create_web_view(self, url_str):
        """Creates a QWebEngineView with the shared profile and loads the URL."""
        web_page = QWebEnginePage(self.profile, self)

        # --- Grant Clipboard Permission ---
        def grant_feature_permission(origin: QUrl, feature: QWebEnginePage.Feature):
            if feature == QWebEnginePage.Feature.ClipboardReadWrite:
                # Grant permission for clipboard access
                web_page.setFeaturePermission(origin, feature, QWebEnginePage.PermissionPolicy.PermissionGrantedByUser)
            else:
                # Default policy for other features
                web_page.setFeaturePermission(origin, feature, QWebEnginePage.PermissionPolicy.PermissionDeniedByUser)

        web_page.featurePermissionRequested.connect(grant_feature_permission)
        # --- End Grant Clipboard Permission ---

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

    def find_in_page(self):
        """Toggle find bar visibility and focus input."""
        if self.find_bar.isVisible():
            self.hide_find_bar()
        else:
            self.find_bar.show()
            self.find_input.setFocus()
            self.find_input.selectAll()

    def hide_find_bar(self):
        """Hide find bar and clear highlights."""
        self.find_bar.hide()
        self.find_input.clear()
        web_view = self.tab_widget.currentWidget()
        if isinstance(web_view, QWebEngineView):
            web_view.findText("")

    def do_find(self, text):
        """Highlight occurrences of `text` in the page."""
        # track current search text and reset index
        self.search_text = text
        self.search_index = 0
        web_view = self.tab_widget.currentWidget()
        if not isinstance(web_view, QWebEngineView):
            return
        # clear previous highlights
        web_view.findText("")
        if not text:
            self.find_label.setText("0/0")
            return
        # try highlighting all occurrences if supported, else highlight first
        from PyQt6.QtWebEngineCore import QWebEnginePage
        flag = getattr(QWebEnginePage.FindFlag, 'HighlightAllOccurrences', None)
        if flag is not None:
            web_view.findText(text, flag)
        else:
            web_view.findText(text)
        # count occurrences via JS and update label
        page = web_view.page()
        escaped = json.dumps(text)
        js = f"(function() {{ var r = new RegExp({escaped}, 'gi'); var m = document.body.innerText.match(r); return m ? m.length : 0; }})()"
        page.runJavaScript(js, self._on_search_count)

    def find_next(self):
        """Move to the next occurrence of the current search text."""
        if not self.search_text or self.search_count == 0:
            return
        # increment index with wrap
        self.search_index = (self.search_index % self.search_count) + 1
        web_view = self.tab_widget.currentWidget()
        if not isinstance(web_view, QWebEngineView):
            return
        from PyQt6.QtWebEngineCore import QWebEnginePage
        # use wrap-around if available
        flag = getattr(QWebEnginePage.FindFlag, 'FindWrapsAroundDocument', QWebEnginePage.FindFlag(0))
        web_view.findText(self.search_text, flag)
        self._update_label()

    def find_prev(self):
        """Move to the previous occurrence of the current search text."""
        if not self.search_text or self.search_count == 0:
            return
        # decrement index with wrap
        self.search_index = ((self.search_index - 2) % self.search_count) + 1
        web_view = self.tab_widget.currentWidget()
        if not isinstance(web_view, QWebEngineView):
            return
        from PyQt6.QtWebEngineCore import QWebEnginePage
        # backward search with wrap-around
        flag = QWebEnginePage.FindFlag.FindBackward
        wrap = getattr(QWebEnginePage.FindFlag, 'FindWrapsAroundDocument', None)
        if wrap is not None:
            flag |= QWebEnginePage.FindFlag.FindWrapsAroundDocument
        web_view.findText(self.search_text, flag)
        self._update_label()

    def _on_search_count(self, count):
        """Callback after JS count. Updates total and sets initial index/label."""
        try:
            self.search_count = int(count)
        except:
            self.search_count = 0
        if self.search_count > 0:
            # first match already highlighted by do_find
            self.search_index = 1
        else:
            self.search_index = 0
        self._update_label()

    def _update_label(self):
        """Update find label to show current index/total."""
        if self.search_count > 0:
            self.find_label.setText(f"{self.search_index}/{self.search_count}")
        else:
            self.find_label.setText("0/0")

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

    def on_tab_context_menu(self, pos):
        """Show context menu on tab right-click."""
        index = self.tab_widget.tabBar().tabAt(pos)
        if index < 0:
            return
        menu = QMenu(self)
        edit_act = menu.addAction("Edit Site")
        remove_act = menu.addAction("Remove Site")
        action = menu.exec(self.tab_widget.tabBar().mapToGlobal(pos))
        if action == edit_act:
            self.edit_site(index)
        elif action == remove_act:
            self.remove_site(index)

    def edit_site(self, index):
        """Edit the name and URL of a site."""
        site = self.sites[index]
        dialog = AddSiteDialog(self)
        dialog.name_input.setText(site['name'])
        dialog.url_input.setText(site['url'])
        if dialog.exec() == AddSiteDialog.DialogCode.Accepted:
            name, url = dialog.get_inputs()
            if not name:
                QMessageBox.warning(self, "Edit Site", "Site Name cannot be empty.")
                return
            if not url:
                QMessageBox.warning(self, "Edit Site", "URL cannot be empty.")
                return
            if not url.startswith("http://") and not url.startswith("https://"):
                url = "https://" + url
            if any(i != index and (s['name'] == name or s['url'] == url) for i, s in enumerate(self.sites)):
                QMessageBox.warning(self, "Edit Site", "A site with this name or URL already exists.")
                return
            self.sites[index] = { 'name': name, 'url': url }
            self.save_sites()
            self.tab_widget.setTabText(index, name)
            web_view = self.web_views[index]
            web_view.setUrl(QUrl(url))

    def remove_site(self, index):
        """Remove a site and its tab."""
        site = self.sites[index]
        # styled confirmation dialog
        dialog = ConfirmDialog(f"Remove site '{site['name']}'?", self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            del self.sites[index]
            self.save_sites()
            self.tab_widget.removeTab(index)
            # rebuild web_views mapping
            self.web_views.clear()
            for idx in range(self.tab_widget.count()):
                self.web_views[idx] = self.tab_widget.widget(idx)
