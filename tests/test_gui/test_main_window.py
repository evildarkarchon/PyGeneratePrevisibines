"""Tests for MainWindow."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QApplication

from PrevisLib.gui.main_window import MainWindow
from PrevisLib.models.data_classes import BuildMode, BuildStep


@pytest.fixture
def qapp() -> QApplication:
    """Create QApplication instance for testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app  # type: ignore[return-value]


@pytest.fixture
def main_window(qapp: QApplication) -> MainWindow:  # noqa: ARG001
    """Create MainWindow for testing."""
    return MainWindow()


class TestMainWindow:
    """Test cases for MainWindow."""

    def test_init(self, main_window: MainWindow) -> None:
        """Test main window initialization."""
        assert main_window.windowTitle() == "PyGeneratePrevisibines"
        assert main_window.minimumSize().width() == 800
        assert main_window.minimumSize().height() == 600
        assert isinstance(main_window.settings, QSettings)

    def test_ui_components_created(self, main_window: MainWindow) -> None:
        """Test that all UI components are created."""
        assert hasattr(main_window, "central_widget")
        assert hasattr(main_window, "main_layout")
        assert hasattr(main_window, "status_bar")
        assert hasattr(main_window, "plugin_input")
        assert hasattr(main_window, "build_controls")
        assert hasattr(main_window, "progress_display")

    def test_menu_bar_created(self, main_window: MainWindow) -> None:
        """Test that menu bar is created with expected menus."""
        menu_bar = main_window.menuBar()
        assert menu_bar is not None

        # Should have File, Settings, and Help menus
        from PyQt6.QtWidgets import QMenu

        menus = [menu for menu in menu_bar.findChildren(QMenu) if menu is not None]
        menu_titles = [menu.title() for menu in menus]
        assert any("File" in title for title in menu_titles)
        assert any("Settings" in title for title in menu_titles)
        assert any("Help" in title for title in menu_titles)

    def test_status_bar_created(self, main_window: MainWindow) -> None:
        """Test that status bar is created and shows initial message."""
        assert main_window.status_bar is not None
        # Note: We can't easily test the initial message due to timing
        assert main_window.statusBar() is main_window.status_bar

    def test_plugin_validation_signal_connection(self, main_window: MainWindow) -> None:
        """Test that plugin validation signal is connected."""
        # Emit validation signal
        main_window.plugin_input.validationStateChanged.emit(True, "Valid plugin")

        # Build controls should be enabled
        assert main_window.build_controls.isEnabled()

    def test_plugin_validation_invalid_disables_build(self, main_window: MainWindow) -> None:
        """Test that invalid plugin disables build controls."""
        # Emit invalid validation signal
        main_window.plugin_input.validationStateChanged.emit(False, "Invalid plugin")

        # Build controls should be disabled
        assert not main_window.build_controls.isEnabled()

    def test_build_controls_signal_connections(self, main_window: MainWindow) -> None:
        """Test that build control signals are connected."""
        # Test that signals are connected (won't raise errors)
        main_window.build_controls.buildStarted.emit(BuildMode.CLEAN, BuildStep.GENERATE_PREVIS)
        main_window.build_controls.buildStopped.emit()

    def test_progress_display_signal_connection(self, main_window: MainWindow) -> None:
        """Test that progress display signal is connected."""
        # Test that signal is connected (won't raise errors)
        main_window.progress_display.cancelConfirmed.emit()

    def test_on_plugin_validation_changed_valid(self, main_window: MainWindow) -> None:
        """Test plugin validation change handler with valid plugin."""
        main_window._on_plugin_validation_changed(True, "Valid plugin")

        assert main_window.build_controls.isEnabled()

    def test_on_plugin_validation_changed_invalid(self, main_window: MainWindow) -> None:
        """Test plugin validation change handler with invalid plugin."""
        main_window._on_plugin_validation_changed(False, "Invalid plugin")

        assert not main_window.build_controls.isEnabled()

    def test_on_build_started(self, main_window: MainWindow) -> None:
        """Test build started handler."""
        mode = BuildMode.FILTERED
        step = BuildStep.GENERATE_PREVIS

        with (
            patch.object(main_window.build_controls, "set_building_state") as mock_set_state,
            patch.object(main_window.progress_display, "start_build") as mock_start_build,
        ):
            main_window._on_build_started(mode, step)

            mock_set_state.assert_called_once_with(True)
            mock_start_build.assert_called_once_with(step)

    def test_on_build_stopped(self, main_window: MainWindow) -> None:
        """Test build stopped handler."""
        with (
            patch.object(main_window.build_controls, "set_building_state") as mock_set_state,
            patch.object(main_window.progress_display, "reset") as mock_reset,
        ):
            main_window._on_build_stopped()

            mock_set_state.assert_called_once_with(False)
            mock_reset.assert_called_once()

    def test_open_preferences(self, main_window: MainWindow) -> None:
        """Test opening preferences dialog."""
        with patch("PrevisLib.gui.settings_dialog.SettingsDialog") as mock_dialog_class:
            mock_dialog = MagicMock()
            mock_dialog.exec.return_value = mock_dialog.DialogCode.Accepted
            mock_dialog_class.return_value = mock_dialog

            main_window._open_preferences()

            # Verify dialog was created and executed
            mock_dialog_class.assert_called_once_with(main_window)
            mock_dialog.exec.assert_called_once()

    def test_show_about(self, main_window: MainWindow) -> None:
        """Test showing about dialog."""
        with patch("PyQt6.QtWidgets.QMessageBox.about") as mock_about:
            main_window._show_about()

            mock_about.assert_called_once()
            args = mock_about.call_args[0]
            assert args[0] is main_window
            assert "About PyGeneratePrevisibines" in args[1]
            assert "PyGeneratePrevisibines" in args[2]

    def test_center_window(self, main_window: MainWindow) -> None:
        """Test window centering."""
        with patch("PyQt6.QtWidgets.QApplication.primaryScreen") as mock_screen:
            from PyQt6.QtCore import QPoint

            mock_screen_obj = MagicMock()
            mock_geometry = MagicMock()
            mock_point = QPoint(100, 100)  # Use real QPoint instead of mock

            # Set up the mock chain
            mock_geometry.center.return_value = mock_point
            mock_screen_obj.availableGeometry.return_value = mock_geometry
            mock_screen.return_value = mock_screen_obj

            # Should not raise errors
            main_window._center_window()

            # Verify the mock was called
            mock_screen.assert_called_once()
            mock_screen_obj.availableGeometry.assert_called_once()

    def test_restore_window_state_with_geometry(self, main_window: MainWindow) -> None:
        """Test restoring window state when geometry is saved."""
        with (
            patch.object(main_window.settings, "value", return_value=b"test_geometry"),
            patch.object(main_window, "restoreGeometry") as mock_restore,
        ):
            main_window._restore_window_state()
            mock_restore.assert_called_once_with(b"test_geometry")

    def test_restore_window_state_without_geometry(self, main_window: MainWindow) -> None:
        """Test restoring window state when no geometry is saved."""
        with (
            patch.object(main_window.settings, "value", return_value=None),
            patch.object(main_window, "_center_window") as mock_center,
        ):
            main_window._restore_window_state()
            mock_center.assert_called_once()

    def test_close_event_saves_state(self, main_window: MainWindow) -> None:
        """Test that close event saves window state."""
        event = MagicMock(spec=QCloseEvent)

        with (
            patch.object(main_window.settings, "setValue") as mock_set_value,
            patch.object(main_window, "saveGeometry", return_value=b"test_geometry") as mock_save,
        ):
            main_window.closeEvent(event)

            mock_save.assert_called_once()
            mock_set_value.assert_called_once_with("geometry", b"test_geometry")
            event.accept.assert_called_once()

    def test_close_event_with_none(self, main_window: MainWindow) -> None:
        """Test close event with None parameter."""
        with patch.object(main_window.settings, "setValue") as mock_set_value:
            # Should not raise errors
            main_window.closeEvent(None)
            mock_set_value.assert_called_once()

    def test_initial_build_controls_disabled(self, main_window: MainWindow) -> None:
        """Test that build controls are initially disabled."""
        assert not main_window.build_controls.isEnabled()

    def test_window_properties(self, main_window: MainWindow) -> None:
        """Test basic window properties."""
        assert main_window.windowTitle() == "PyGeneratePrevisibines"
        assert main_window.centralWidget() is main_window.central_widget

    def test_settings_organization(self, main_window: MainWindow) -> None:
        """Test QSettings organization and application name."""
        settings = main_window.settings
        assert settings.organizationName() == "PyGeneratePrevisibines"
        assert settings.applicationName() == "MainWindow"

    def test_layout_structure(self, main_window: MainWindow) -> None:
        """Test that layout contains expected widgets."""
        layout = main_window.main_layout

        # Check that widgets are added to layout
        widget_count = layout.count()
        assert widget_count > 0

        # Should contain plugin input, build controls, and progress display
        widgets_in_layout = []
        for i in range(widget_count):
            item = layout.itemAt(i)
            if item and item.widget():
                widgets_in_layout.append(item.widget())

        assert main_window.plugin_input in widgets_in_layout
        assert main_window.build_controls in widgets_in_layout
        assert main_window.progress_display in widgets_in_layout

    def test_menu_actions_exist(self, main_window: MainWindow) -> None:
        """Test that menu actions exist and are connected."""
        menu_bar = main_window.menuBar()
        assert menu_bar is not None

        # Find all menus
        from PyQt6.QtWidgets import QMenu

        menus = menu_bar.findChildren(QMenu)

        # Get all actions from all menus
        all_actions = []
        for menu in menus:
            all_actions.extend(menu.actions())

        # Get action texts
        action_texts = [action.text() for action in all_actions if action.text()]
        # Remove ampersands from text for comparison
        clean_texts = [text.replace("&", "") for text in action_texts]

        assert any("Exit" in text for text in clean_texts)
        assert any("Preferences" in text for text in clean_texts)
        assert any("About" in text for text in clean_texts)

        # Check that actions have shortcuts where expected
        exit_actions = [action for action in all_actions if "Exit" in action.text() or "xit" in action.text()]
        if exit_actions:
            assert exit_actions[0].shortcut().toString() == "Ctrl+Q"

        preferences_actions = [action for action in all_actions if "Preferences" in action.text()]
        if preferences_actions:
            assert preferences_actions[0].shortcut().toString() == "Ctrl+,"

    def test_status_bar_message_updates(self, main_window: MainWindow) -> None:
        """Test status bar message updates."""
        # Test plugin validation message
        main_window._on_plugin_validation_changed(False, "Test error")
        # Status bar should show error (we can't easily test exact message due to timing)

        # Test build started message
        main_window._on_build_started(BuildMode.CLEAN, BuildStep.GENERATE_PREVIS)
        # Status bar should show build started message

        # Test build stopped message
        main_window._on_build_stopped()
        # Status bar should show build stopped message

    def test_widget_initialization_order(self, main_window: MainWindow) -> None:
        """Test that widgets are initialized in the correct order."""
        # All widgets should be properly initialized
        assert main_window.plugin_input is not None
        assert main_window.build_controls is not None
        assert main_window.progress_display is not None

        # Signal connections should be established
        # (We can't easily test this directly, but if initialization worked,
        # the signals should be connected)
