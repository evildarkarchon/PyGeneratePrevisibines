"""Tests for utility modules."""

from unittest.mock import Mock, patch

import pytest

from PrevisLib.utils.file_system import clean_directory, ensure_directory, find_files, safe_delete
from PrevisLib.utils.logging import get_logger, setup_logger
from PrevisLib.utils.process import ProcessRunner, run_process


class TestFileOperations:
    """Test file operation utilities."""

    def test_ensure_directory(self, tmp_path):
        """Test directory creation."""
        test_dir = tmp_path / "test" / "nested" / "directory"

        ensure_directory(test_dir)

        assert test_dir.exists()
        assert test_dir.is_dir()

    def test_ensure_existing_directory(self, tmp_path):
        """Test ensuring an already existing directory."""
        test_dir = tmp_path / "existing"
        test_dir.mkdir()

        # Should not raise an error
        ensure_directory(test_dir)
        assert test_dir.exists()

    def test_clean_directory(self, tmp_path):
        """Test directory cleaning."""
        test_dir = tmp_path / "test_clean"
        test_dir.mkdir()
        test_file = test_dir / "file.txt"
        test_file.write_text("content")

        clean_directory(test_dir)

        assert test_dir.exists()
        assert not test_file.exists()

    def test_safe_delete(self, tmp_path):
        """Test safe file deletion."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        result = safe_delete(test_file)

        assert result is True
        assert not test_file.exists()

    def test_find_files(self, tmp_path):
        """Test file finding."""
        test_files = [tmp_path / "file1.txt", tmp_path / "file2.txt", tmp_path / "subdir" / "file3.txt"]

        for file_path in test_files:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text("content")

        found_files = find_files(tmp_path, "*.txt")
        assert len(found_files) == 3


class TestProcessRunner:
    """Test process execution utilities."""

    def test_initialization(self):
        """Test ProcessRunner initialization."""
        runner = ProcessRunner()
        assert runner is not None

    @patch("PrevisLib.utils.process.subprocess.run")
    def test_successful_execution(self, mock_run):
        """Test successful process execution."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "success output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        runner = ProcessRunner()
        result = runner.execute(["echo", "test"])

        assert result is True

    @patch("PrevisLib.utils.process.subprocess.run")
    def test_failed_execution(self, mock_run):
        """Test failed process execution."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error message"
        mock_run.return_value = mock_result

        runner = ProcessRunner()
        result = runner.execute(["false"])

        assert result is False

    @patch("PrevisLib.utils.process.subprocess.run")
    def test_run_process_function(self, mock_run):
        """Test run_process function directly."""
        # Mock successful process execution
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "test output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = run_process(["echo", "test"])

        assert result.returncode == 0
        assert result.success is True


class TestLogging:
    """Test logging utilities."""

    def test_setup_logger(self):
        """Test logger setup."""
        logger = setup_logger("test_logger")

        assert logger is not None
        # loguru logger doesn't have a .name attribute

    def test_get_logger(self):
        """Test getting logger instance."""
        logger1 = get_logger("test_module")
        logger2 = get_logger("test_module")

        # Both should be loguru logger instances (same global logger)
        assert logger1 is not None
        assert logger2 is not None

    def test_logger_basic_functionality(self):
        """Test basic logger functionality."""
        logger = get_logger("basic_test")

        # Should be able to call logging methods without error
        try:
            logger.info("test message")
            logger.debug("debug message")
            logger.error("error message")
        except Exception as e:
            pytest.fail(f"Logger methods should not raise exceptions: {e}")

        assert logger is not None
