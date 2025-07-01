"""Main window for PyGeneratePrevisibines GUI."""

from typing import Any

from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtGui import QAction, QCloseEvent
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from gui.widgets.plugin_input import PluginInputWidget


class MainWindow(QMainWindow):
    """Main application window for PyGeneratePrevisibines GUI."""

    def __init__(self) -> None:
        """Initialize the main window."""
        super().__init__()
        
        # Settings for window state persistence
        self.settings = QSettings("PyGeneratePrevisibines", "MainWindow")
        
        # Initialize UI
        self._init_ui()
        
        # Restore window state
        self._restore_window_state()
    
    def _init_ui(self) -> None:
        """Initialize the user interface."""
        # Set window properties
        self.setWindowTitle("PyGeneratePrevisibines")
        self.setMinimumSize(800, 600)
        
        # Create central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        
        # Create menu bar
        self._create_menu_bar()
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Add plugin input widget
        self.plugin_input = PluginInputWidget()
        self.plugin_input.validationStateChanged.connect(self._on_plugin_validation_changed)
        self.main_layout.addWidget(self.plugin_input)
        
        # Add stretch to push everything to the top
        self.main_layout.addStretch()
        
    def _create_menu_bar(self) -> None:
        """Create the application menu bar."""
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("&File")
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Settings menu
        settings_menu = menu_bar.addMenu("&Settings")
        
        # Preferences action
        preferences_action = QAction("&Preferences...", self)
        preferences_action.setShortcut("Ctrl+,")
        preferences_action.setStatusTip("Open preferences dialog")
        preferences_action.triggered.connect(self._open_preferences)
        settings_menu.addAction(preferences_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("&Help")
        
        # About action
        about_action = QAction("&About", self)
        about_action.setStatusTip("Show information about the application")
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _restore_window_state(self) -> None:
        """Restore window size and position from settings."""
        # Restore geometry
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            # Center window on screen
            self._center_window()
    
    def _center_window(self) -> None:
        """Center the window on the primary screen."""
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            window_geometry = self.frameGeometry()
            window_geometry.moveCenter(screen_geometry.center())
            self.move(window_geometry.topLeft())
    
    def _open_preferences(self) -> None:
        """Open the preferences dialog."""
        # TODO: Implement settings dialog
        self.status_bar.showMessage("Settings dialog not yet implemented", 3000)
    
    def _show_about(self) -> None:
        """Show the about dialog."""
        QMessageBox.about(
            self,
            "About PyGeneratePrevisibines",
            "<h3>PyGeneratePrevisibines</h3>"
            "<p>A Python port of PJM's GeneratePrevisibines batch file for Fallout 4.</p>"
            "<p>This tool automates the generation of precombined meshes and previs data "
            "for Fallout 4 mods, which are essential for game performance optimization.</p>"
        )
    
    def _on_plugin_validation_changed(self, is_valid: bool, message: str) -> None:
        """Handle plugin validation state changes.
        
        Args:
            is_valid: Whether the plugin name is valid
            message: Validation message
        """
        if message and not is_valid:
            # Show error in status bar for invalid plugins
            self.status_bar.showMessage(f"Plugin validation: {message}", 5000)
        else:
            self.status_bar.clearMessage()
    
    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event."""
        # Save window state
        self.settings.setValue("geometry", self.saveGeometry())
        
        # Accept the close event
        event.accept()