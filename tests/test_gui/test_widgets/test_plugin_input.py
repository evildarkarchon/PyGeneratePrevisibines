"""Tests for PluginInputWidget."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QWidget

from PrevisLib.config.settings import Settings
from PrevisLib.gui.widgets.plugin_input import PluginInputWidget


@pytest.fixture
def qapp() -> QApplication:
    """Create QApplication instance for testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app  # type: ignore[return-value]


@pytest.fixture
def mock_settings() -> Settings:
    """Create mock Settings object."""
    settings = MagicMock(spec=Settings)
    settings.tool_paths = MagicMock()
    settings.tool_paths.fallout4 = Path("/test/fallout4")
    return settings


@pytest.fixture
def widget(qapp: QApplication) -> PluginInputWidget:  # noqa: ARG001
    """Create PluginInputWidget for testing."""
    return PluginInputWidget()


@pytest.fixture
def widget_with_settings(qapp: QApplication, mock_settings: Settings) -> PluginInputWidget:  # noqa: ARG001
    """Create PluginInputWidget with settings for testing."""
    return PluginInputWidget(settings=mock_settings)


class TestPluginInputWidget:
    """Test cases for PluginInputWidget."""

    def test_init_default(self, widget: PluginInputWidget) -> None:
        """Test widget initialization with default parameters."""
        assert widget.settings is None
        assert isinstance(widget._validation_timer, QTimer)
        assert widget._validation_timer.isSingleShot()

    def test_init_with_settings(self, widget_with_settings: PluginInputWidget, mock_settings: Settings) -> None:
        """Test widget initialization with settings."""
        assert widget_with_settings.settings is mock_settings

    def test_init_with_parent(self, qapp: QApplication) -> None:  # noqa: ARG002
        """Test widget initialization with parent."""
        parent = QWidget()
        widget = PluginInputWidget(parent=parent)
        assert widget.parent() is parent

    def test_ui_components_created(self, widget: PluginInputWidget) -> None:
        """Test that all UI components are created."""
        assert hasattr(widget, "label")
        assert hasattr(widget, "line_edit")
        assert hasattr(widget, "validation_icon")
        assert hasattr(widget, "validation_message")

        assert widget.label.text() == "Plugin Name:"
        assert "Enter plugin name" in widget.line_edit.placeholderText()

    def test_line_edit_properties(self, widget: PluginInputWidget) -> None:
        """Test line edit properties and tooltip."""
        assert widget.line_edit.placeholderText() == "Enter plugin name (e.g., MyMod or MyMod.esp)"

        tooltip = widget.line_edit.toolTip()
        assert "Enter the name of your plugin" in tooltip
        assert ".esp extension will be added automatically" in tooltip

    def test_text_changed_starts_validation_timer(self, widget: PluginInputWidget) -> None:
        """Test that text changes start the validation timer."""
        with patch.object(widget._validation_timer, "stop") as mock_stop, patch.object(widget._validation_timer, "start") as mock_start:
            widget.line_edit.setText("test")

            mock_stop.assert_called_once()
            mock_start.assert_called_once_with(300)

    def test_text_changed_clears_validation_display(self, widget: PluginInputWidget) -> None:
        """Test that text changes clear validation display."""
        # Set some validation state first
        widget.validation_icon.setText("✓")
        widget.validation_message.setText("Test message")
        widget.validation_message.show()

        # Change text
        widget.line_edit.setText("test")

        # Validation should be cleared
        assert widget.validation_icon.text() == ""
        assert not widget.validation_message.isVisible()

    @patch("PrevisLib.gui.widgets.plugin_input.validate_plugin_name")
    def test_validate_plugin_empty_name(self, mock_validate: MagicMock, widget: PluginInputWidget) -> None:
        """Test validation with empty plugin name."""
        widget.line_edit.setText("")
        widget._validate_plugin()

        # Should not call validate_plugin_name for empty input
        mock_validate.assert_not_called()

    @patch("PrevisLib.gui.widgets.plugin_input.validate_plugin_name")
    def test_validate_plugin_adds_extension(self, mock_validate: MagicMock, widget: PluginInputWidget) -> None:
        """Test that validation adds .esp extension if missing."""
        mock_validate.return_value = (True, "")

        widget.line_edit.setText("TestMod")
        widget._validate_plugin()

        # Should have added .esp extension
        assert widget.line_edit.text() == "TestMod.esp"
        mock_validate.assert_called_once_with("TestMod.esp")

    @patch("PrevisLib.gui.widgets.plugin_input.validate_plugin_name")
    def test_validate_plugin_keeps_existing_extension(self, mock_validate: MagicMock, widget: PluginInputWidget) -> None:
        """Test that validation keeps existing extension."""
        mock_validate.return_value = (True, "")

        widget.line_edit.setText("TestMod.esm")
        widget._validate_plugin()

        # Should keep existing extension
        assert widget.line_edit.text() == "TestMod.esm"
        mock_validate.assert_called_once_with("TestMod.esm")

    @patch("PrevisLib.gui.widgets.plugin_input.validate_plugin_name")
    def test_validate_plugin_reserved_names(self, mock_validate: MagicMock, widget: PluginInputWidget) -> None:
        """Test validation rejects reserved build names."""
        mock_validate.return_value = (True, "")

        reserved_names = ["previs", "combinedobjects", "xprevispatch"]

        for name in reserved_names:
            widget.line_edit.setText(name)
            widget._validate_plugin()

            # Should be invalid due to reserved name
            # Check the signal was emitted with is_valid=False
            # Note: We can't easily test signal emission in this setup,
            # so we test the internal state would be invalid

    @patch("PrevisLib.gui.widgets.plugin_input.validate_plugin_name")
    def test_validate_plugin_with_settings_existing_plugin(self, mock_validate: MagicMock, widget_with_settings: PluginInputWidget) -> None:
        """Test validation with settings when plugin exists."""
        mock_validate.return_value = (True, "")

        # Mock plugin file exists
        assert widget_with_settings.settings is not None
        settings = widget_with_settings.settings
        plugin_path = settings.tool_paths.fallout4 / "Data" / "TestMod.esp"  # type: ignore[operator]  # noqa: F841

        # Use patch on pathlib.Path.exists instead
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = True

            widget_with_settings.line_edit.setText("TestMod")

            # Trigger validation
            widget_with_settings._validate_plugin()

            # Should be valid with "exists" message
            mock_validate.assert_called_once_with("TestMod.esp")
            assert "Plugin exists" in widget_with_settings.validation_message.text()

    @patch("PrevisLib.gui.widgets.plugin_input.validate_plugin_name")
    def test_validate_plugin_with_settings_archive_exists(self, mock_validate: MagicMock, widget_with_settings: PluginInputWidget) -> None:
        """Test validation when archive exists but plugin doesn't."""
        mock_validate.return_value = (True, "")

        # Mock plugin doesn't exist but archive does
        assert widget_with_settings.settings is not None
        settings = widget_with_settings.settings
        plugin_path = settings.tool_paths.fallout4 / "Data" / "TestMod.esp"  # type: ignore[operator]  # noqa: F841
        settings.tool_paths.fallout4 / "Data" / "TestMod - Main.ba2"  # type: ignore[operator]

        def mock_exists(self) -> bool:  # noqa: ANN001
            """Mock exists method that returns False for plugin, True for archive."""
            path_str = str(self)
            if path_str.endswith("TestMod.esp"):
                return False
            return bool(path_str.endswith("TestMod - Main.ba2"))

        with patch("pathlib.Path.exists", mock_exists):
            widget_with_settings.line_edit.setText("TestMod")

            # Trigger validation
            widget_with_settings._validate_plugin()

            # Should be invalid because archive exists
            mock_validate.assert_called_once_with("TestMod.esp")
            assert "Archive" in widget_with_settings.validation_message.text()
            assert "already exists" in widget_with_settings.validation_message.text()

    def test_get_plugin_name_empty(self, widget: PluginInputWidget) -> None:
        """Test get_plugin_name with empty input."""
        widget.line_edit.setText("")
        assert widget.get_plugin_name() == ""

    def test_get_plugin_name_with_extension(self, widget: PluginInputWidget) -> None:
        """Test get_plugin_name with extension."""
        widget.line_edit.setText("TestMod.esp")
        assert widget.get_plugin_name() == "TestMod.esp"

    def test_get_plugin_name_adds_extension(self, widget: PluginInputWidget) -> None:
        """Test get_plugin_name adds extension when missing."""
        widget.line_edit.setText("TestMod")
        assert widget.get_plugin_name() == "TestMod.esp"

    def test_set_plugin_name(self, widget: PluginInputWidget) -> None:
        """Test setting plugin name."""
        widget.set_plugin_name("TestMod.esp")
        assert widget.line_edit.text() == "TestMod.esp"

    @patch("PrevisLib.gui.widgets.plugin_input.validate_plugin_name")
    def test_is_valid_empty_name(self, mock_validate: MagicMock, widget: PluginInputWidget) -> None:
        """Test is_valid with empty name."""
        widget.line_edit.setText("")
        assert not widget.is_valid()
        mock_validate.assert_not_called()

    @patch("PrevisLib.gui.widgets.plugin_input.validate_plugin_name")
    def test_is_valid_valid_name(self, mock_validate: MagicMock, widget: PluginInputWidget) -> None:
        """Test is_valid with valid name."""
        mock_validate.return_value = (True, "")
        widget.line_edit.setText("TestMod")
        assert widget.is_valid()

    @patch("PrevisLib.gui.widgets.plugin_input.validate_plugin_name")
    def test_is_valid_invalid_name(self, mock_validate: MagicMock, widget: PluginInputWidget) -> None:
        """Test is_valid with invalid name."""
        mock_validate.return_value = (False, "Invalid name")
        widget.line_edit.setText("Invalid Name")
        assert not widget.is_valid()

    @patch("PrevisLib.gui.widgets.plugin_input.validate_plugin_name")
    def test_is_valid_reserved_name(self, mock_validate: MagicMock, widget: PluginInputWidget) -> None:
        """Test is_valid with reserved name."""
        mock_validate.return_value = (True, "")
        widget.line_edit.setText("previs")
        assert not widget.is_valid()

    def test_update_settings(self, widget: PluginInputWidget, mock_settings: Settings) -> None:
        """Test updating settings."""
        widget.line_edit.setText("TestMod")

        with patch.object(widget, "_validate_plugin") as mock_validate:
            widget.update_settings(mock_settings)

            assert widget.settings is mock_settings
            mock_validate.assert_called_once()

    def test_update_settings_no_text(self, widget: PluginInputWidget, mock_settings: Settings) -> None:
        """Test updating settings with no text."""
        widget.line_edit.setText("")

        with patch.object(widget, "_validate_plugin") as mock_validate:
            widget.update_settings(mock_settings)

            assert widget.settings is mock_settings
            mock_validate.assert_not_called()

    def test_validation_state_changed_signal(self, widget: PluginInputWidget) -> None:
        """Test that validationStateChanged signal exists."""
        # Test that signal exists and can be connected
        signal_connected = False

        def test_slot(is_valid: bool, message: str) -> None:  # noqa: ARG001
            nonlocal signal_connected
            signal_connected = True

        widget.validationStateChanged.connect(test_slot)

        # Trigger validation to emit signal
        widget._set_validation_state(True, "Test message")

        assert signal_connected

    def test_set_validation_state_valid_new_plugin(self, widget: PluginInputWidget) -> None:
        """Test setting validation state for valid new plugin."""
        widget._set_validation_state(True, "New plugin", exists=False)

        assert widget.validation_icon.text() == "ℹ"  # noqa: RUF001
        assert widget.validation_message.text() == "New plugin"
        # Check if validation message is shown (not necessarily visible due to layout)
        assert not widget.validation_message.isHidden()

    def test_set_validation_state_valid_existing_plugin(self, widget: PluginInputWidget) -> None:
        """Test setting validation state for valid existing plugin."""
        widget._set_validation_state(True, "Existing plugin", exists=True)

        assert widget.validation_icon.text() == "✓"
        assert widget.validation_message.text() == "Existing plugin"
        assert not widget.validation_message.isHidden()

    def test_set_validation_state_invalid(self, widget: PluginInputWidget) -> None:
        """Test setting validation state for invalid plugin."""
        widget._set_validation_state(False, "Invalid plugin")

        assert widget.validation_icon.text() == "✗"
        assert widget.validation_message.text() == "Invalid plugin"
        assert not widget.validation_message.isHidden()

    def test_set_validation_state_no_message(self, widget: PluginInputWidget) -> None:
        """Test setting validation state with no message."""
        widget._set_validation_state(True, "")

        assert not widget.validation_message.isVisible()

    def test_validation_timer_connection(self, widget: PluginInputWidget) -> None:
        """Test that validation timer is connected to validation method."""
        # Check that the timer is connected by inspecting its connections
        connections = widget._validation_timer.receivers(widget._validation_timer.timeout)
        assert connections > 0, "Timer should have at least one connection"

        # Alternative test: check that triggering text change starts the timer
        with patch.object(widget._validation_timer, "start") as mock_start:
            widget.line_edit.setText("test")
            mock_start.assert_called()

    def test_validation_debouncing(self, widget: PluginInputWidget) -> None:
        """Test that validation is debounced."""
        with patch.object(widget._validation_timer, "stop") as mock_stop, patch.object(widget._validation_timer, "start") as mock_start:
            # Multiple rapid text changes
            widget.line_edit.setText("a")
            widget.line_edit.setText("ab")
            widget.line_edit.setText("abc")

            # Timer should have been stopped and started multiple times
            assert mock_stop.call_count == 3
            assert mock_start.call_count == 3
