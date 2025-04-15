import sys
import importlib.resources
from PyQt6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon
from PyQt6.QtGui import QIcon

from .app import MainWindow

def main():
    app = QApplication(sys.argv)
    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "Systray", "I couldn't detect any system tray on this system.")
        sys.exit(1)

    app.setQuitOnLastWindowClosed(False)

    # IMPORTANT for StandardPaths and persistent storage location
    app.setOrganizationName("chAIt")
    app.setApplicationName("chAIt")

    try:
        stylesheet_content = importlib.resources.read_text('chait', 'styles/style.css')
        app.setStyleSheet(stylesheet_content)
    except ModuleNotFoundError:
         print("Error: Could not find the 'chait' package to load resources from.", file=sys.stderr)
    except FileNotFoundError:
         print("Error: Stylesheet resource 'styles/style.css' not found within the 'chait' package.", file=sys.stderr)
    except Exception as e:
        print(f"Warning: Could not load stylesheet resource: {e}", file=sys.stderr)

    try:
        icon_ref = importlib.resources.files('chait').joinpath('assets/icon.png')
        with importlib.resources.as_file(icon_ref) as icon_path:
            if icon_path.is_file():
                app_icon = QIcon(str(icon_path))
                app.setWindowIcon(app_icon)
            else:
                print(f"Warning: Icon resource path is not a file: {icon_path}", file=sys.stderr)
    except ModuleNotFoundError:
         print("Error: Could not find the 'chait' package to load resources from.", file=sys.stderr)
    except FileNotFoundError:
         print("Error: Icon resource 'assets/icon.png' not found within the 'chait' package.", file=sys.stderr)
    except Exception as e:
        print(f"Warning: Could not load icon resource: {e}", file=sys.stderr)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
