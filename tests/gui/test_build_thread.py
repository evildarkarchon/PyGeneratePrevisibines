"""Tests for the build thread module."""

from unittest.mock import MagicMock, Mock, patch

import pytest
from PyQt6.QtCore import QCoreApplication, QThread
from PyQt6.QtTest import QSignalSpy

from PrevisLib.config.settings import Settings
from PrevisLib.gui.build_thread import BuildThread
from PrevisLib.models.data_classes import BuildMode, BuildStep, BuildStatus, ToolPaths


@pytest.fixture
def qt_app():
    """Create a Qt application for testing."""
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    yield app
    app.quit()


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    settings = Mock(spec=Settings)
    settings.plugin_name = "TestPlugin.esp"
    settings.build_mode = BuildMode.CLEAN
    settings.tool_paths = Mock(spec=ToolPaths)
    return settings


class TestBuildThread:
    """Test cases for BuildThread class."""

    def test_init(self, mock_settings):
        """Test BuildThread initialization."""
        thread = BuildThread(mock_settings)
        
        assert thread.settings == mock_settings
        assert thread.start_from_step is None
        assert thread.builder is None
        assert thread._cancelled is False

    def test_init_with_start_step(self, mock_settings):
        """Test BuildThread initialization with start step."""
        thread = BuildThread(mock_settings, BuildStep.ARCHIVE_MESHES)
        
        assert thread.start_from_step == BuildStep.ARCHIVE_MESHES

    @patch('PrevisLib.gui.build_thread.PrevisBuilder')
    @patch('PrevisLib.gui.build_thread.logger')
    def test_run_success(self, mock_logger, mock_builder_class, mock_settings, qt_app):
        """Test successful build run."""
        # Create mock builder
        mock_builder = MagicMock()
        mock_builder.build.return_value = True
        mock_builder.failed_step = None
        mock_builder.current_step = BuildStep.GENERATE_PRECOMBINED
        mock_builder_class.return_value = mock_builder
        
        # Create thread
        thread = BuildThread(mock_settings)
        
        # Set up signal spies
        completed_spy = QSignalSpy(thread.build_completed)
        failed_spy = QSignalSpy(thread.build_failed)
        
        # Run thread
        thread.run()
        
        # Verify builder was created and called
        mock_builder_class.assert_called_once_with(mock_settings)
        mock_builder.build.assert_called_once_with(None)
        
        # Verify signals
        assert len(completed_spy) == 1
        assert len(failed_spy) == 0
        
        # Verify logger was hooked
        mock_logger.add.assert_called_once()

    @patch('PrevisLib.gui.build_thread.PrevisBuilder')
    @patch('PrevisLib.gui.build_thread.logger')
    def test_run_failure(self, mock_logger, mock_builder_class, mock_settings, qt_app):
        """Test failed build run."""
        # Create mock builder
        mock_builder = MagicMock()
        mock_builder.build.return_value = False
        mock_builder.failed_step = BuildStep.MERGE_COMBINED_OBJECTS
        mock_builder.current_step = BuildStep.MERGE_COMBINED_OBJECTS
        mock_builder_class.return_value = mock_builder
        
        # Create thread
        thread = BuildThread(mock_settings)
        
        # Set up signal spies
        completed_spy = QSignalSpy(thread.build_completed)
        failed_spy = QSignalSpy(thread.build_failed)
        
        # Run thread
        thread.run()
        
        # Verify signals
        assert len(completed_spy) == 0
        assert len(failed_spy) == 1
        assert failed_spy[0][0] == BuildStep.MERGE_COMBINED_OBJECTS
        assert failed_spy[0][1] == "Build process failed"

    @patch('PrevisLib.gui.build_thread.PrevisBuilder')
    @patch('PrevisLib.gui.build_thread.logger')
    def test_run_exception(self, mock_logger, mock_builder_class, mock_settings, qt_app):
        """Test build run with exception."""
        # Create mock builder that raises exception
        mock_builder = MagicMock()
        mock_builder.build.side_effect = ValueError("Test error")
        mock_builder.current_step = BuildStep.GENERATE_PREVIS
        mock_builder_class.return_value = mock_builder
        
        # Create thread
        thread = BuildThread(mock_settings)
        
        # Set up signal spy
        failed_spy = QSignalSpy(thread.build_failed)
        
        # Run thread
        thread.run()
        
        # Verify signals
        assert len(failed_spy) == 1
        assert failed_spy[0][0] == BuildStep.GENERATE_PREVIS
        assert "Test error" in failed_spy[0][1]
        
        # Verify exception was logged
        mock_logger.exception.assert_called_once()

    @patch('PrevisLib.gui.build_thread.PrevisBuilder')
    def test_cancel(self, mock_builder_class, mock_settings):
        """Test build cancellation."""
        mock_builder = MagicMock()
        mock_builder_class.return_value = mock_builder
        
        thread = BuildThread(mock_settings)
        thread.builder = mock_builder
        
        # Cancel thread
        thread.cancel()
        
        assert thread._cancelled is True
        assert mock_builder.cancel_requested is True

    @patch('PrevisLib.gui.build_thread.PrevisBuilder')
    def test_progress_callback(self, mock_builder_class, mock_settings, qt_app):
        """Test progress callback functionality."""
        # Create thread
        thread = BuildThread(mock_settings)
        
        # Set up signal spies
        step_started_spy = QSignalSpy(thread.step_started)
        step_completed_spy = QSignalSpy(thread.step_completed)
        step_progress_spy = QSignalSpy(thread.step_progress)
        failed_spy = QSignalSpy(thread.build_failed)
        
        # Test different status callbacks
        thread._progress_callback(BuildStep.GENERATE_PRECOMBINED, BuildStatus.RUNNING, "Starting")
        assert len(step_started_spy) == 1
        assert step_started_spy[0][0] == BuildStep.GENERATE_PRECOMBINED
        
        thread._progress_callback(BuildStep.GENERATE_PRECOMBINED, BuildStatus.RUNNING, "Processing")
        assert len(step_progress_spy) == 2  # Two RUNNING callbacks = two progress signals
        assert step_progress_spy[1][0] == BuildStep.GENERATE_PRECOMBINED
        assert step_progress_spy[1][2] == "Processing"
        
        thread._progress_callback(BuildStep.GENERATE_PRECOMBINED, BuildStatus.COMPLETED, "Done")
        assert len(step_completed_spy) == 1
        assert step_completed_spy[0][0] == BuildStep.GENERATE_PRECOMBINED
        
        thread._progress_callback(BuildStep.GENERATE_PRECOMBINED, BuildStatus.FAILED, "Error occurred")
        assert len(failed_spy) == 1
        assert failed_spy[0][0] == BuildStep.GENERATE_PRECOMBINED
        assert failed_spy[0][1] == "Error occurred"

    @patch('PrevisLib.gui.build_thread.PrevisBuilder')
    def test_progress_callback_cancelled(self, mock_builder_class, mock_settings, qt_app):
        """Test progress callback when cancelled."""
        thread = BuildThread(mock_settings)
        thread._cancelled = True
        
        # Set up signal spy
        step_started_spy = QSignalSpy(thread.step_started)
        
        # Callback should not emit signals when cancelled
        thread._progress_callback(BuildStep.GENERATE_PRECOMBINED, BuildStatus.RUNNING, "Starting")
        assert len(step_started_spy) == 0

    def test_log_handler(self, mock_settings, qt_app):
        """Test log message handler."""
        thread = BuildThread(mock_settings)
        
        # Set up signal spy
        log_spy = QSignalSpy(thread.log_message)
        
        # Create mock log message
        from datetime import datetime
        mock_level = Mock()
        mock_level.name = "ERROR"
        mock_message = {
            "time": datetime.now(),
            "level": mock_level,
            "message": "Test error message"
        }
        
        # Handle log message
        thread._log_handler(mock_message)
        
        # Verify signal
        assert len(log_spy) == 1
        assert log_spy[0][1] == "ERROR"
        assert log_spy[0][2] == "Test error message"

    def test_log_handler_cancelled(self, mock_settings, qt_app):
        """Test log handler when cancelled."""
        thread = BuildThread(mock_settings)
        thread._cancelled = True
        
        # Set up signal spy
        log_spy = QSignalSpy(thread.log_message)
        
        # Create mock log message
        from datetime import datetime
        mock_message = {
            "time": datetime.now(),
            "level": Mock(name="INFO"),
            "message": "Test message"
        }
        
        # Handle log message - should not emit when cancelled
        thread._log_handler(mock_message)
        assert len(log_spy) == 0

    @patch('PrevisLib.gui.build_thread.PrevisBuilder')
    def test_progress_callback_assignment(self, mock_builder_class, mock_settings):
        """Test that progress callback is properly assigned to builder."""
        mock_builder = MagicMock()
        mock_builder_class.return_value = mock_builder
        
        thread = BuildThread(mock_settings)
        thread.run()
        
        # Verify progress callback was assigned
        assert mock_builder.progress_callback == thread._progress_callback