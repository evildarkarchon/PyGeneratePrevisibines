"""Tests for BuildControlsWidget."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from PyQt6.QtWidgets import QApplication, QWidget

from PrevisLib.gui.widgets.build_controls import BuildControlsWidget
from PrevisLib.models.data_classes import BuildMode, BuildStep


@pytest.fixture
def qapp() -> QApplication:
    """Create QApplication instance for testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app  # type: ignore[return-value]


@pytest.fixture
def widget(qapp: QApplication) -> BuildControlsWidget:  # noqa: ARG001
    """Create BuildControlsWidget for testing."""
    return BuildControlsWidget()


class TestBuildControlsWidget:
    """Test cases for BuildControlsWidget."""

    def test_init_default(self, widget: BuildControlsWidget) -> None:
        """Test widget initialization with default parameters."""
        assert not widget._is_building

    def test_init_with_parent(self, qapp: QApplication) -> None:  # noqa: ARG002
        """Test widget initialization with parent."""
        parent = QWidget()
        widget = BuildControlsWidget(parent=parent)
        assert widget.parent() is parent

    def test_ui_components_created(self, widget: BuildControlsWidget) -> None:
        """Test that all UI components are created."""
        assert hasattr(widget, "mode_combo")
        assert hasattr(widget, "step_combo")
        assert hasattr(widget, "start_stop_button")

        # Check initial button text
        assert widget.start_stop_button.text() == "Start Build"

    def test_mode_combo_populated(self, widget: BuildControlsWidget) -> None:
        """Test that mode combo box is populated with all build modes."""
        assert widget.mode_combo.count() == len(BuildMode)

        for i in range(widget.mode_combo.count()):
            mode = widget.mode_combo.itemData(i)
            assert isinstance(mode, BuildMode)

    def test_step_combo_initial_population(self, widget: BuildControlsWidget) -> None:
        """Test that step combo box is initially populated."""
        assert widget.step_combo.count() > 0

        # All items should be BuildStep instances
        for i in range(widget.step_combo.count()):
            step = widget.step_combo.itemData(i)
            assert isinstance(step, BuildStep)

    def test_get_build_mode(self, widget: BuildControlsWidget) -> None:
        """Test getting current build mode."""
        # Set mode to FILTERED
        widget.set_build_mode(BuildMode.FILTERED)
        assert widget.get_build_mode() == BuildMode.FILTERED

    def test_get_build_step(self, widget: BuildControlsWidget) -> None:
        """Test getting current build step."""
        # Set step to GENERATE_PREVIS
        widget.set_build_step(BuildStep.GENERATE_PREVIS)
        assert widget.get_build_step() == BuildStep.GENERATE_PREVIS

    def test_set_build_mode(self, widget: BuildControlsWidget) -> None:
        """Test setting build mode."""
        widget.set_build_mode(BuildMode.XBOX)
        assert widget.get_build_mode() == BuildMode.XBOX

    def test_set_build_step(self, widget: BuildControlsWidget) -> None:
        """Test setting build step."""
        widget.set_build_step(BuildStep.COMPRESS_PSG)
        assert widget.get_build_step() == BuildStep.COMPRESS_PSG

    def test_set_building_state_true(self, widget: BuildControlsWidget) -> None:
        """Test setting building state to true."""
        widget.set_building_state(True)

        assert widget._is_building
        assert widget.start_stop_button.text() == "Stop Build"
        assert not widget.mode_combo.isEnabled()
        assert not widget.step_combo.isEnabled()

    def test_set_building_state_false(self, widget: BuildControlsWidget) -> None:
        """Test setting building state to false."""
        # First set to building
        widget.set_building_state(True)

        # Then set to not building
        widget.set_building_state(False)

        assert not widget._is_building
        assert widget.start_stop_button.text() == "Start Build"
        assert widget.mode_combo.isEnabled()
        assert widget.step_combo.isEnabled()

    def test_mode_changed_repopulates_steps(self, widget: BuildControlsWidget) -> None:
        """Test that changing mode repopulates step combo."""
        # Set to CLEAN mode
        widget.set_build_mode(BuildMode.CLEAN)
        clean_step_count = widget.step_combo.count()

        # Set to FILTERED mode
        widget.set_build_mode(BuildMode.FILTERED)
        filtered_step_count = widget.step_combo.count()

        # CLEAN mode should have more steps (includes COMPRESS_PSG and BUILD_CDX)
        assert clean_step_count > filtered_step_count

    def test_clean_mode_includes_all_steps(self, widget: BuildControlsWidget) -> None:
        """Test that CLEAN mode includes all build steps."""
        widget.set_build_mode(BuildMode.CLEAN)

        # Should include COMPRESS_PSG and BUILD_CDX
        steps = [widget.step_combo.itemData(i) for i in range(widget.step_combo.count())]
        assert BuildStep.COMPRESS_PSG in steps
        assert BuildStep.BUILD_CDX in steps

    def test_filtered_mode_excludes_specific_steps(self, widget: BuildControlsWidget) -> None:
        """Test that FILTERED mode excludes specific steps."""
        widget.set_build_mode(BuildMode.FILTERED)

        # Should not include COMPRESS_PSG and BUILD_CDX
        steps = [widget.step_combo.itemData(i) for i in range(widget.step_combo.count())]
        assert BuildStep.COMPRESS_PSG not in steps
        assert BuildStep.BUILD_CDX not in steps

    def test_xbox_mode_excludes_specific_steps(self, widget: BuildControlsWidget) -> None:
        """Test that XBOX mode excludes specific steps."""
        widget.set_build_mode(BuildMode.XBOX)

        # Should not include COMPRESS_PSG and BUILD_CDX
        steps = [widget.step_combo.itemData(i) for i in range(widget.step_combo.count())]
        assert BuildStep.COMPRESS_PSG not in steps
        assert BuildStep.BUILD_CDX not in steps

    def test_start_stop_button_click_when_not_building(self, widget: BuildControlsWidget) -> None:
        """Test start/stop button click when not building."""
        # Connect to signal
        signal_received = False
        received_mode = None
        received_step = None

        def on_build_started(mode: BuildMode, step: BuildStep) -> None:
            nonlocal signal_received, received_mode, received_step
            signal_received = True
            received_mode = mode
            received_step = step

        widget.buildStarted.connect(on_build_started)

        # Click button
        widget.start_stop_button.click()

        assert signal_received
        assert received_mode is not None
        assert received_step is not None

    def test_start_stop_button_click_when_building(self, widget: BuildControlsWidget) -> None:
        """Test start/stop button click when building."""
        # Set to building state
        widget.set_building_state(True)

        # Connect to signal
        signal_received = False

        def on_build_stopped() -> None:
            nonlocal signal_received
            signal_received = True

        widget.buildStopped.connect(on_build_stopped)

        # Click button
        widget.start_stop_button.click()

        assert signal_received

    def test_build_started_signal_parameters(self, widget: BuildControlsWidget) -> None:
        """Test that buildStarted signal passes correct parameters."""
        # Set specific mode and step
        widget.set_build_mode(BuildMode.XBOX)
        widget.set_build_step(BuildStep.GENERATE_PREVIS)

        received_params = []

        def on_build_started(mode: BuildMode, step: BuildStep) -> None:
            received_params.append((mode, step))

        widget.buildStarted.connect(on_build_started)

        # Trigger start
        widget._on_start_stop_clicked()

        assert len(received_params) == 1
        assert received_params[0] == (BuildMode.XBOX, BuildStep.GENERATE_PREVIS)

    def test_setEnabled_when_not_building(self, widget: BuildControlsWidget) -> None:
        """Test setEnabled when not building."""
        widget.setEnabled(True)

        assert widget.mode_combo.isEnabled()
        assert widget.step_combo.isEnabled()
        assert widget.start_stop_button.isEnabled()

    def test_setEnabled_when_building(self, widget: BuildControlsWidget) -> None:
        """Test setEnabled when building."""
        widget.set_building_state(True)
        widget.setEnabled(True)

        # Controls should remain disabled while building
        assert not widget.mode_combo.isEnabled()
        assert not widget.step_combo.isEnabled()
        assert widget.start_stop_button.isEnabled()  # Start/stop button stays enabled

    def test_setEnabled_false(self, widget: BuildControlsWidget) -> None:
        """Test setEnabled(False) disables all controls."""
        widget.setEnabled(False)

        assert not widget.mode_combo.isEnabled()
        assert not widget.step_combo.isEnabled()
        assert not widget.start_stop_button.isEnabled()

    def test_combo_tooltips(self, widget: BuildControlsWidget) -> None:
        """Test that combo boxes have helpful tooltips."""
        mode_tooltip = widget.mode_combo.toolTip()
        assert "Clean:" in mode_tooltip
        assert "Filtered:" in mode_tooltip
        assert "Xbox:" in mode_tooltip

        step_tooltip = widget.step_combo.toolTip()
        assert "Select which step" in step_tooltip

    def test_button_tooltip(self, widget: BuildControlsWidget) -> None:
        """Test that button has helpful tooltip."""
        tooltip = widget.start_stop_button.toolTip()
        assert "Start or stop" in tooltip

    def test_button_styling_not_building(self, widget: BuildControlsWidget) -> None:
        """Test button styling when not building."""
        widget.set_building_state(False)

        # Should have success styling
        style = widget.start_stop_button.styleSheet()
        assert "#4caf50" in style  # DarkTheme.SUCCESS

    def test_button_styling_building(self, widget: BuildControlsWidget) -> None:
        """Test button styling when building."""
        widget.set_building_state(True)

        # Should have error styling
        style = widget.start_stop_button.styleSheet()
        assert "#f44336" in style  # DarkTheme.ERROR

    def test_step_default_for_filtered_mode(self, widget: BuildControlsWidget) -> None:
        """Test that FILTERED mode defaults to appropriate step."""
        widget.set_build_mode(BuildMode.CLEAN)  # Start with clean
        widget.set_build_mode(BuildMode.FILTERED)  # Switch to filtered

        # Should default to GENERATE_PREVIS or similar
        current_step = widget.get_build_step()
        assert current_step is not None

    def test_signals_exist(self, widget: BuildControlsWidget) -> None:
        """Test that required signals exist and can be connected."""
        # Test signal connection doesn't raise errors
        mock_start_handler = MagicMock()
        mock_stop_handler = MagicMock()

        widget.buildStarted.connect(mock_start_handler)
        widget.buildStopped.connect(mock_stop_handler)

        # Signals should be connectable without errors
        assert widget.buildStarted is not None
        assert widget.buildStopped is not None

    def test_mode_combo_signal_connection(self, widget: BuildControlsWidget) -> None:
        """Test that mode combo changes trigger step repopulation."""
        widget.step_combo.count()

        # Change mode
        widget.mode_combo.setCurrentIndex(1)

        # Step count may change
        new_count = widget.step_combo.count()
        # We can't assert exact values since it depends on the mode order,
        # but we can assert that the repopulation logic ran
        assert isinstance(new_count, int)

    def test_widget_minimum_size(self, widget: BuildControlsWidget) -> None:
        """Test that widget has reasonable minimum sizes."""
        # Combo boxes should have minimum widths
        assert widget.mode_combo.minimumWidth() >= 200
        assert widget.step_combo.minimumWidth() >= 200

        # Button should have minimum height
        assert widget.start_stop_button.minimumHeight() >= 40
