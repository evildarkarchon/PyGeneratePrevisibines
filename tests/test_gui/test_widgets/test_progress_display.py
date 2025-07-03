"""Tests for ProgressDisplayWidget."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QWidget

from PrevisLib.gui.widgets.progress_display import ProgressDisplayWidget
from PrevisLib.models.data_classes import BuildStatus, BuildStep


@pytest.fixture
def qapp() -> QApplication:
    """Create QApplication instance for testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app  # type: ignore[return-value]


@pytest.fixture
def widget(qapp: QApplication) -> ProgressDisplayWidget:  # noqa: ARG001
    """Create ProgressDisplayWidget for testing."""
    return ProgressDisplayWidget()


class TestProgressDisplayWidget:
    """Test cases for ProgressDisplayWidget."""

    def test_init_default(self, widget: ProgressDisplayWidget) -> None:
        """Test widget initialization with default parameters."""
        assert len(widget._step_statuses) == len(BuildStep)
        for step in BuildStep:
            assert widget._step_statuses[step] == BuildStatus.PENDING
        assert widget._current_step is None
        assert widget._start_time is None
        assert not widget.isVisible()  # Initially hidden
        assert isinstance(widget._timer, QTimer)

    def test_init_with_parent(self, qapp: QApplication) -> None:  # noqa: ARG002
        """Test widget initialization with parent."""
        parent = QWidget()
        widget = ProgressDisplayWidget(parent=parent)
        assert widget.parent() is parent

    def test_ui_components_created(self, widget: ProgressDisplayWidget) -> None:
        """Test that all UI components are created."""
        assert hasattr(widget, "current_step_label")
        assert hasattr(widget, "step_counter_label")
        assert hasattr(widget, "time_elapsed_label")
        assert hasattr(widget, "step_list")

        # Check initial state
        assert widget.current_step_label.text() == "Ready to build"
        assert widget.step_counter_label.text() == "Step 0 of 8"
        assert widget.time_elapsed_label.text() == "Time: 00:00:00"

    def test_initially_hidden(self, widget: ProgressDisplayWidget) -> None:
        """Test that widget is initially hidden."""
        assert not widget.isVisible()

    def test_step_statuses_initialization(self, widget: ProgressDisplayWidget) -> None:
        """Test that step statuses are initialized correctly."""
        widget._reset_progress()

        # Should have status for all build steps
        assert len(widget._step_statuses) == len(BuildStep)

        # All should be pending initially
        for step, status in widget._step_statuses.items():
            assert isinstance(step, BuildStep)
            assert status == BuildStatus.PENDING

    def test_start_build(self, widget: ProgressDisplayWidget) -> None:
        """Test starting a build process."""
        start_step = BuildStep.GENERATE_PREVIS

        with patch("PrevisLib.gui.widgets.progress_display.datetime") as mock_datetime:
            mock_now = datetime(2023, 1, 1, 12, 0, 0)
            mock_datetime.now.return_value = mock_now

            widget.start_build(start_step)

            assert widget._start_time == mock_now
            assert widget._current_step == start_step
            assert widget._step_statuses[start_step] == BuildStatus.RUNNING
            assert widget.isVisible()

    def test_start_build_updates_ui(self, widget: ProgressDisplayWidget) -> None:
        """Test that start_build updates the UI correctly."""
        start_step = BuildStep.COMPRESS_PSG

        widget.start_build(start_step)

        assert f"Running: {start_step!s}" in widget.current_step_label.text()
        assert "Step 4 of 8" in widget.step_counter_label.text()
        assert widget.isVisible()
        assert widget._current_step == start_step
        assert widget._start_time is not None

    def test_start_build_starts_timer(self, widget: ProgressDisplayWidget) -> None:
        """Test that start_build starts the timer."""
        with patch.object(widget._timer, "start") as mock_start:
            widget.start_build(BuildStep.GENERATE_PREVIS)
            mock_start.assert_called_once_with(1000)

    def test_update_step_status(self, widget: ProgressDisplayWidget) -> None:
        """Test updating step status."""
        step = BuildStep.GENERATE_PREVIS
        widget.update_step_status(step, BuildStatus.SUCCESS)

        assert widget._step_statuses[step] == BuildStatus.SUCCESS

    def test_update_step_status_running(self, widget: ProgressDisplayWidget) -> None:
        """Test updating step status to running updates current step."""
        step = BuildStep.BUILD_CDX
        widget.update_step_status(step, BuildStatus.RUNNING)

        assert widget._current_step == step
        assert f"Running: {step!s}" in widget.current_step_label.text()

    def test_complete_build_success(self, widget: ProgressDisplayWidget) -> None:
        """Test completing build successfully."""
        # Start build first
        widget.start_build(BuildStep.GENERATE_PREVIS)

        with patch.object(widget._timer, "stop") as mock_stop:
            widget.complete_build(True)

            mock_stop.assert_called_once()
            assert "Build completed successfully!" in widget.current_step_label.text()
            assert "Step 8 of 8" in widget.step_counter_label.text()

    def test_complete_build_failure(self, widget: ProgressDisplayWidget) -> None:
        """Test completing build with failure."""
        # Start build first
        widget.start_build(BuildStep.GENERATE_PREVIS)

        with patch.object(widget._timer, "stop") as mock_stop:
            widget.complete_build(False)

            mock_stop.assert_called_once()
            assert "Build failed!" in widget.current_step_label.text()
            assert "Failed at step" in widget.step_counter_label.text()

    def test_reset(self, widget: ProgressDisplayWidget) -> None:
        """Test resetting the widget."""
        # Start build first
        widget.start_build(BuildStep.GENERATE_PREVIS)

        with patch.object(widget._timer, "stop") as mock_stop:
            widget.reset()

            mock_stop.assert_called_once()
            assert widget._start_time is None
            assert widget._current_step is None
            assert not widget.isVisible()

    def test_get_status_icon(self, widget: ProgressDisplayWidget) -> None:
        """Test getting status icons for different states."""
        widget._step_statuses[BuildStep.GENERATE_PREVIS] = BuildStatus.PENDING
        assert widget._get_status_icon(BuildStep.GENERATE_PREVIS) == "⏳"

        widget._step_statuses[BuildStep.GENERATE_PREVIS] = BuildStatus.RUNNING
        assert widget._get_status_icon(BuildStep.GENERATE_PREVIS) == "🔄"

        widget._step_statuses[BuildStep.GENERATE_PREVIS] = BuildStatus.SUCCESS
        assert widget._get_status_icon(BuildStep.GENERATE_PREVIS) == "✅"

        widget._step_statuses[BuildStep.GENERATE_PREVIS] = BuildStatus.FAILED
        assert widget._get_status_icon(BuildStep.GENERATE_PREVIS) == "❌"

    def test_get_status_color(self, widget: ProgressDisplayWidget) -> None:
        """Test getting status colors for different states."""
        from PrevisLib.gui.styles.dark_theme import DarkTheme

        widget._step_statuses[BuildStep.GENERATE_PREVIS] = BuildStatus.PENDING
        assert widget._get_status_color(BuildStep.GENERATE_PREVIS) == DarkTheme.TEXT_SECONDARY

        widget._step_statuses[BuildStep.GENERATE_PREVIS] = BuildStatus.RUNNING
        assert widget._get_status_color(BuildStep.GENERATE_PREVIS) == DarkTheme.ACCENT

        widget._step_statuses[BuildStep.GENERATE_PREVIS] = BuildStatus.SUCCESS
        assert widget._get_status_color(BuildStep.GENERATE_PREVIS) == DarkTheme.SUCCESS

        widget._step_statuses[BuildStep.GENERATE_PREVIS] = BuildStatus.FAILED
        assert widget._get_status_color(BuildStep.GENERATE_PREVIS) == DarkTheme.ERROR

    def test_get_current_step_number(self, widget: ProgressDisplayWidget) -> None:
        """Test getting current step number."""
        # No current step
        assert widget._get_current_step_number() == 0

        # Set current step
        widget._current_step = BuildStep.GENERATE_PREVIS
        step_number = widget._get_current_step_number()
        assert step_number > 0
        assert step_number <= len(BuildStep)

    def test_update_elapsed_time(self, widget: ProgressDisplayWidget) -> None:
        """Test updating elapsed time display."""
        with patch("PrevisLib.gui.widgets.progress_display.datetime") as mock_datetime:
            start_time = datetime(2023, 1, 1, 12, 0, 0)
            current_time = datetime(2023, 1, 1, 12, 1, 30)  # 1 minute 30 seconds later

            widget._start_time = start_time
            mock_datetime.now.return_value = current_time

            widget._update_elapsed_time()

            assert "Time: 00:01:30" in widget.time_elapsed_label.text()

    def test_update_elapsed_time_no_start_time(self, widget: ProgressDisplayWidget) -> None:
        """Test updating elapsed time when no start time is set."""
        widget._start_time = None
        original_text = widget.time_elapsed_label.text()

        widget._update_elapsed_time()

        # Should not change the text
        assert widget.time_elapsed_label.text() == original_text

    def test_populate_step_list(self, widget: ProgressDisplayWidget) -> None:
        """Test populating the step list."""
        widget._populate_step_list()

        # Should have items for all build steps
        assert widget.step_list.count() == len(BuildStep)

        # Check that items contain step information
        for i in range(widget.step_list.count()):
            item = widget.step_list.item(i)
            assert item is not None
            step = item.data(256)
            assert isinstance(step, BuildStep)

    def test_update_step_list_item(self, widget: ProgressDisplayWidget) -> None:
        """Test updating a specific step in the list."""
        widget._populate_step_list()

        # Update a step status
        step = BuildStep.GENERATE_PREVIS
        widget._step_statuses[step] = BuildStatus.SUCCESS
        widget._update_step_list_item(step)

        # Find the item for this step
        for i in range(widget.step_list.count()):
            item = widget.step_list.item(i)
            if item and item.data(256) == step:
                assert "✅" in item.text()
                break
        else:
            pytest.fail(f"Could not find item for step {step}")

    def test_timer_connection(self, widget: ProgressDisplayWidget) -> None:
        """Test that timer is connected to update method."""
        # Check that the timer is connected by inspecting its connections
        connections = widget._timer.receivers(widget._timer.timeout)
        assert connections > 0, "Timer should have at least one connection"

        # Alternative test: check that starting build starts the timer
        with patch.object(widget._timer, "start") as mock_start:
            widget.start_build(BuildStep.GENERATE_PREVIS)
            mock_start.assert_called_with(1000)

    def test_request_cancel_confirmed(self, widget: ProgressDisplayWidget) -> None:
        """Test cancel request confirmation."""
        signal_emitted = False

        def on_cancel_confirmed() -> None:
            nonlocal signal_emitted
            signal_emitted = True

        widget.cancelConfirmed.connect(on_cancel_confirmed)

        # Mock the message box to return Yes
        with patch("PyQt6.QtWidgets.QMessageBox.question", return_value=0x00004000):  # Yes button
            widget.request_cancel()
            assert signal_emitted

    def test_request_cancel_rejected(self, widget: ProgressDisplayWidget) -> None:
        """Test cancel request rejection."""
        signal_emitted = False

        def on_cancel_confirmed() -> None:
            nonlocal signal_emitted
            signal_emitted = True

        widget.cancelConfirmed.connect(on_cancel_confirmed)

        # Mock the message box to return No
        with patch("PyQt6.QtWidgets.QMessageBox.question", return_value=0x00010000):  # No button
            widget.request_cancel()
            assert not signal_emitted

    def test_cancel_confirmed_signal_exists(self, widget: ProgressDisplayWidget) -> None:
        """Test that cancelConfirmed signal exists and can be connected."""
        mock_handler = MagicMock()
        widget.cancelConfirmed.connect(mock_handler)

        # Signal should be connectable without errors
        assert widget.cancelConfirmed is not None

    def test_step_status_enum_values(self) -> None:
        """Test that BuildStatus enum has expected values."""
        assert BuildStatus.PENDING
        assert BuildStatus.RUNNING
        assert BuildStatus.SUCCESS
        assert BuildStatus.FAILED

        # Test enum values are unique
        values = [status.value for status in BuildStatus]
        assert len(values) == len(set(values))

    def test_elapsed_time_formatting(self, widget: ProgressDisplayWidget) -> None:
        """Test various elapsed time formats."""
        test_cases = [
            (0, "Time: 00:00:00"),
            (30, "Time: 00:00:30"),
            (90, "Time: 00:01:30"),
            (3661, "Time: 01:01:01"),
            (7200, "Time: 02:00:00"),
        ]

        for seconds, expected in test_cases:
            with patch("PrevisLib.gui.widgets.progress_display.datetime") as mock_datetime:
                start_time = datetime(2023, 1, 1, 12, 0, 0)
                from datetime import timedelta

                current_time = start_time + timedelta(seconds=seconds)

                mock_datetime.now.return_value = current_time
                widget._start_time = start_time

                widget._update_elapsed_time()

                assert widget.time_elapsed_label.text() == expected

    def test_step_list_styling(self, widget: ProgressDisplayWidget) -> None:
        """Test that step list has proper styling."""
        style = widget.step_list.styleSheet()

        # Should contain styling properties
        assert "background-color" in style
        assert "border" in style
        assert "padding" in style
