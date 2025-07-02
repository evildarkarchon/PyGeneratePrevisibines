"""Main window for PyGeneratePrevisibines GUI."""

from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QAction, QCloseEvent
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from PrevisLib.config.settings import Settings
from PrevisLib.gui.build_thread import BuildThread
from PrevisLib.gui.widgets.build_controls import BuildControlsWidget
from PrevisLib.gui.widgets.plugin_input import PluginInputWidget
from PrevisLib.gui.widgets.progress_display import ProgressDisplayWidget
from PrevisLib.models.data_classes import BuildMode, BuildStatus, BuildStep, ToolPaths


class MainWindow(QMainWindow):
    """Main application window for PyGeneratePrevisibines GUI."""

    def __init__(self) -> None:
        """Initialize the main window."""
        super().__init__()

        # Settings for window state persistence
        self.settings = QSettings("PyGeneratePrevisibines", "MainWindow")
        
        # Build thread reference
        self.build_thread: BuildThread | None = None

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

        # Add build controls widget
        self.build_controls = BuildControlsWidget()
        self.build_controls.buildStarted.connect(self._on_build_started)
        self.build_controls.buildStopped.connect(self._on_build_stopped)
        self.main_layout.addWidget(self.build_controls)

        # Disable build controls until a valid plugin is entered
        self.build_controls.setEnabled(False)

        # Add progress display widget
        self.progress_display = ProgressDisplayWidget()
        self.progress_display.cancelConfirmed.connect(self._on_build_stopped)
        self.main_layout.addWidget(self.progress_display)

        # Add stretch to push everything to the top
        self.main_layout.addStretch()

    def _create_menu_bar(self) -> None:
        """Create the application menu bar."""
        menu_bar = self.menuBar()
        if not menu_bar:
            return

        # File menu
        file_menu = menu_bar.addMenu("&File")
        if not file_menu:
            return

        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Settings menu
        settings_menu = menu_bar.addMenu("&Settings")
        if not settings_menu:
            return

        # Preferences action
        preferences_action = QAction("&Preferences...", self)
        preferences_action.setShortcut("Ctrl+,")
        preferences_action.setStatusTip("Open preferences dialog")
        preferences_action.triggered.connect(self._open_preferences)
        settings_menu.addAction(preferences_action)

        # Help menu
        help_menu = menu_bar.addMenu("&Help")
        if not help_menu:
            return

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
        from PrevisLib.gui.settings_dialog import SettingsDialog

        dialog = SettingsDialog(self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            # Settings were saved, update status
            self.status_bar.showMessage("Settings saved successfully", 3000)
        else:
            self.status_bar.showMessage("Settings dialog cancelled", 2000)

    def _show_about(self) -> None:
        """Show the about dialog."""
        QMessageBox.about(
            self,
            "About PyGeneratePrevisibines",
            "<h3>PyGeneratePrevisibines</h3>"
            "<p>A Python port of PJM's GeneratePrevisibines batch file for Fallout 4.</p>"
            "<p>This tool automates the generation of precombined meshes and previs data "
            "for Fallout 4 mods, which are essential for game performance optimization.</p>",
        )

    def _on_plugin_validation_changed(self, is_valid: bool, message: str) -> None:
        """Handle plugin validation state changes.

        Args:
            is_valid: Whether the plugin name is valid
            message: Validation message
        """
        # Enable/disable build controls based on validation
        self.build_controls.setEnabled(is_valid)

        if message and not is_valid:
            # Show error in status bar for invalid plugins
            self.status_bar.showMessage(f"Plugin validation: {message}", 5000)
        else:
            self.status_bar.clearMessage()

    def _on_build_started(self, mode: BuildMode, step: BuildStep) -> None:
        """Handle build start signal.

        Args:
            mode: Build mode
            step: Starting build step
        """
        self.status_bar.showMessage(f"Build started: {mode.value} mode from {step}")

        # Update build controls state
        self.build_controls.set_building_state(True)

        # Start progress display
        self.progress_display.start_build(step)

        # Get tool paths from settings dialog or use defaults
        tool_paths = self._get_tool_paths()
        if not tool_paths:
            QMessageBox.critical(self, "Configuration Error", "Tool paths not configured. Please configure in Settings.")
            self._on_build_stopped()
            return
        
        # Create settings for build
        build_settings = Settings(
            plugin_name=self.plugin_input.get_plugin_name(),
            build_mode=mode,
            tool_paths=tool_paths
        )
        
        # Create and start build thread
        self.build_thread = BuildThread(build_settings, step if step != BuildStep.GENERATE_PRECOMBINED else None)
        
        # Connect signals
        self.build_thread.step_started.connect(self._on_step_started)
        self.build_thread.step_progress.connect(self._on_step_progress)
        self.build_thread.step_completed.connect(self._on_step_completed)
        self.build_thread.build_completed.connect(self._on_build_completed)
        self.build_thread.build_failed.connect(self._on_build_failed)
        self.build_thread.log_message.connect(self._on_log_message)
        
        # Start the thread
        self.build_thread.start()

    def _on_build_stopped(self) -> None:
        """Handle build stop signal."""
        self.status_bar.showMessage("Build stopped by user", 3000)

        # Update build controls state
        self.build_controls.set_building_state(False)

        # Reset progress display
        self.progress_display.reset()

        # Stop the build thread if running
        if self.build_thread and self.build_thread.isRunning():
            self.build_thread.cancel()
            self.build_thread.wait(5000)  # Wait up to 5 seconds
            
            if self.build_thread.isRunning():
                # Force terminate if still running
                self.build_thread.terminate()
                self.build_thread.wait()
                
            self.build_thread = None

    def _get_tool_paths(self) -> ToolPaths | None:
        """Get tool paths from configuration.
        
        Returns:
            ToolPaths object if configured, None otherwise
        """
        # TODO: This should come from settings dialog or config file
        # For now, return None to trigger the error message
        return None
        
    def _on_step_started(self, step: BuildStep) -> None:
        """Handle step started signal.
        
        Args:
            step: The build step that started
        """
        self.progress_display.update_step_status(step, BuildStatus.RUNNING)
        
    def _on_step_progress(self, step: BuildStep, _percentage: int, message: str) -> None:
        """Handle step progress signal.
        
        Args:
            step: Current build step
            percentage: Progress percentage (0-100)
            message: Progress message
        """
        # Update status bar with progress message
        self.status_bar.showMessage(f"{step}: {message}")
        
    def _on_step_completed(self, step: BuildStep) -> None:
        """Handle step completed signal.
        
        Args:
            step: The build step that completed
        """
        self.progress_display.update_step_status(step, BuildStatus.COMPLETED)
        
    def _on_build_completed(self) -> None:
        """Handle build completed signal."""
        self.status_bar.showMessage("Build completed successfully!", 5000)
        self.build_controls.set_building_state(False)
        
        # Show success dialog
        QMessageBox.information(
            self,
            "Build Complete",
            "Previs build completed successfully!"
        )
        
        self.build_thread = None
        
    def _on_build_failed(self, step: BuildStep, error_message: str) -> None:
        """Handle build failed signal.
        
        Args:
            step: The step that failed
            error_message: Error description
        """
        self.progress_display.update_step_status(step, BuildStatus.FAILED)
        self.status_bar.showMessage(f"Build failed at {step}", 5000)
        self.build_controls.set_building_state(False)
        
        # Show error dialog
        QMessageBox.critical(
            self,
            "Build Failed",
            f"Build failed at step: {step}\n\nError: {error_message}"
        )
        
        self.build_thread = None
        
    def _on_log_message(self, _timestamp: str, level: str, message: str) -> None:
        """Handle log message signal.
        
        Args:
            timestamp: Message timestamp
            level: Log level
            message: Log message
        """
        # TODO: Add to log viewer widget when implemented
        # For now, just update status bar for important messages
        if level in ("ERROR", "WARNING", "SUCCESS"):
            self.status_bar.showMessage(f"[{level}] {message}", 3000)

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        """Handle window close event."""
        # Save window state
        self.settings.setValue("geometry", self.saveGeometry())

        # Accept the close event if it exists
        if a0:
            a0.accept()
