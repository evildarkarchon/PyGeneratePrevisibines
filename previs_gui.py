"""GUI entry point for PyGeneratePrevisibines."""

import sys
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow
from gui.styles.dark_theme import DarkTheme


def main() -> None:
    """Main entry point for the GUI application."""
    # Create application
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("PyGeneratePrevisibines")
    app.setOrganizationName("PyGeneratePrevisibines")
    
    # Apply dark theme
    DarkTheme.apply_theme(app)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()