PREFIX ?= /usr
PYTHON = python3
PIP = $(PYTHON) -m pip

APP_DIR = $(DESTDIR)$(PREFIX)/share/applications
ICON_DIR = $(DESTDIR)$(PREFIX)/share/icons/hicolor/64x64/apps
PIXMAP_DIR = $(DESTDIR)$(PREFIX)/share/pixmaps

DESKTOP_FILE = chait.desktop
ICON_SOURCE = chait/assets/icon.png
ICON_TARGET_NAME = chait.png

.PHONY: install uninstall run clean check_dirs

all:
	@echo "Usage: make [install|uninstall|run|clean]"

check_dirs:
	@if [ ! -d "chait/assets" ] || [ ! -f "$(ICON_SOURCE)" ]; then \
		echo "Error: 'chait/assets' directory or '$(ICON_SOURCE)' not found."; \
		exit 1; \
	fi
	@if [ ! -d "chait/styles" ] || [ ! -f "chait/styles/style.css" ]; then \
		echo "Error: 'chait/styles' directory or 'chait/styles/style.css' not found."; \
		exit 1; \
	fi
	@if [ ! -f "$(DESKTOP_FILE)" ]; then \
		echo "Error: '$(DESKTOP_FILE)' not found."; \
		exit 1; \
	fi

install: check_dirs
	@echo "Installing chAIt system-wide..."
	sudo $(PIP) install .
	@echo "Installing desktop file and icon..."
	sudo mkdir -p $(APP_DIR)
	sudo cp $(DESKTOP_FILE) $(APP_DIR)/
	sudo mkdir -p $(ICON_DIR)
	sudo cp $(ICON_SOURCE) $(ICON_DIR)/$(ICON_TARGET_NAME)
	@echo "Updating caches..."
	sudo update-desktop-database $(APP_DIR) || echo "Warning: update-desktop-database failed."
	sudo gtk-update-icon-cache $(PREFIX)/share/icons/hicolor/ -f || echo "Warning: gtk-update-icon-cache failed."
	@echo "Installation complete. Run with 'chait' or find it in your application menu."

uninstall:
	@echo "Uninstalling chAIt..."
	sudo $(PIP) uninstall -y chait
	@echo "Removing desktop file and icon..."
	sudo rm -f $(APP_DIR)/$(DESKTOP_FILE)
	sudo rm -f $(ICON_DIR)/$(ICON_TARGET_NAME)
	@echo "Updating caches..."
	sudo update-desktop-database $(APP_DIR) || echo "Warning: update-desktop-database failed."
	sudo gtk-update-icon-cache $(PREFIX)/share/icons/hicolor/ -f || echo "Warning: gtk-update-icon-cache failed."
	@echo "Uninstallation complete."

run:
	@echo "Running chAIt from source..."
	$(PYTHON) -m chait

clean:
	@echo "Cleaning build artifacts..."
	$(PYTHON) setup.py clean --all
	rm -rf build dist *.egg-info .pytest_cache .coverage htmlcov *.pyc
	rm -rf chait/__pycache__
	@echo "Clean complete."

