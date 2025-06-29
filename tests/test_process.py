"""Tests for process execution utilities."""

import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock, patch

from PrevisLib.utils.process import (
    ProcessResult,
    ProcessRunner,
    check_process_running,
    kill_process,
    run_process,
    run_with_window_automation,
)


class TestProcessResult:
    """Test ProcessResult class."""

    def test_initialization(self) -> None:
        """Test ProcessResult initialization."""
        result = ProcessResult(0, "stdout", "stderr", 1.5)

        assert result.returncode == 0
        assert result.stdout == "stdout"
        assert result.stderr == "stderr"
        assert result.elapsed_time == 1.5
        assert result.success is True

    def test_success_property(self) -> None:
        """Test success property for different return codes."""
        success_result = ProcessResult(0, "", "", 1.0)
        assert success_result.success is True

        failure_result = ProcessResult(1, "", "", 1.0)
        assert failure_result.success is False

        error_result = ProcessResult(-1, "", "", 1.0)
        assert error_result.success is False


class TestRunProcess:
    """Test run_process function."""

    @patch("PrevisLib.utils.process.subprocess.run")
    @patch("PrevisLib.utils.process.time.perf_counter")
    def test_successful_execution(self, mock_perf_counter: MagicMock, mock_run: MagicMock) -> None:
        """Test successful process execution."""
        mock_perf_counter.side_effect = [0.0, 1.5]  # start and end times

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "success output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = run_process(["echo", "test"])

        assert result.returncode == 0
        assert result.stdout == "success output"
        assert result.stderr == ""
        assert result.elapsed_time == 1.5
        assert result.success is True

    @patch("PrevisLib.utils.process.subprocess.run")
    @patch("PrevisLib.utils.process.time.perf_counter")
    def test_failed_execution(self, mock_perf_counter: MagicMock, mock_run: MagicMock) -> None:
        """Test failed process execution."""
        mock_perf_counter.side_effect = [0.0, 2.0]

        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error message"
        mock_run.return_value = mock_result

        result = run_process(["false"])

        assert result.returncode == 1
        assert result.stdout == ""
        assert result.stderr == "error message"
        assert result.elapsed_time == 2.0
        assert result.success is False

    @patch("PrevisLib.utils.process.subprocess.run")
    def test_timeout_handling(self, mock_run: MagicMock) -> None:
        """Test process timeout handling."""
        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 30)

        result = run_process(["sleep", "60"], timeout=30)

        assert result.returncode == -1
        assert "timed out" in result.stderr
        assert result.success is False

    @patch("PrevisLib.utils.process.subprocess.run")
    def test_exception_handling(self, mock_run: MagicMock) -> None:
        """Test exception handling during process execution."""
        mock_run.side_effect = OSError("Command not found")

        result = run_process(["nonexistent_command"])

        assert result.returncode == -1
        assert "Command not found" in result.stderr
        assert result.success is False

    @patch("PrevisLib.utils.process.subprocess.run")
    def test_string_command(self, mock_run: MagicMock) -> None:
        """Test running command as string."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = run_process("echo test")

        assert result.success is True
        # Should be split into list
        mock_run.assert_called_once()

    @patch("PrevisLib.utils.process.subprocess.run")
    def test_shell_command(self, mock_run: MagicMock) -> None:
        """Test running command with shell=True."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = run_process("echo test", shell=True)

        assert result.success is True
        # Should pass string as-is when shell=True
        call_args = mock_run.call_args
        assert call_args[1]["shell"] is True

    @patch("PrevisLib.utils.process.subprocess.run")
    def test_working_directory(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test running command in specific directory."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = run_process(["pwd"], cwd=tmp_path)

        assert result.success is True
        call_args = mock_run.call_args
        assert call_args[1]["cwd"] == tmp_path

    @patch("PrevisLib.utils.process.subprocess.run")
    def test_capture_output_false(self, mock_run: MagicMock) -> None:
        """Test running command without capturing output."""
        mock_result = Mock()
        mock_result.returncode = 0
        # No stdout/stderr when not captured
        del mock_result.stdout
        del mock_result.stderr
        mock_run.return_value = mock_result

        result = run_process(["echo", "test"], capture_output=False)

        assert result.success is True
        assert result.stdout == ""
        assert result.stderr == ""

    @patch("PrevisLib.utils.process.subprocess.run")
    def test_environment_variables(self, mock_run: MagicMock) -> None:
        """Test running command with custom environment."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        env = {"TEST_VAR": "test_value"}
        result = run_process(["env"], env=env)

        assert result.success is True
        call_args = mock_run.call_args
        assert call_args[1]["env"] == env


class TestProcessRunner:
    """Test ProcessRunner class."""

    def test_initialization(self) -> None:
        """Test ProcessRunner initialization."""
        runner = ProcessRunner()
        assert runner is not None

    @patch("PrevisLib.utils.process.run_process")
    def test_run_process_success(self, mock_run_process: MagicMock) -> None:
        """Test ProcessRunner.execute with successful execution."""
        mock_result = Mock()
        mock_result.success = True
        mock_run_process.return_value = mock_result

        runner = ProcessRunner()
        result = runner.execute(["echo", "test"])

        assert result is True
        mock_run_process.assert_called_once()

    @patch("PrevisLib.utils.process.run_process")
    def test_run_process_failure(self, mock_run_process: MagicMock) -> None:
        """Test ProcessRunner.execute with failed execution."""
        mock_result = Mock()
        mock_result.success = False
        mock_run_process.return_value = mock_result

        runner = ProcessRunner()
        result = runner.execute(["false"])

        assert result is False

    @patch("PrevisLib.utils.process.run_process")
    def test_run_process_with_options(self, mock_run_process: MagicMock) -> None:
        """Test ProcessRunner.execute with various options."""
        mock_result = Mock()
        mock_result.success = True
        mock_run_process.return_value = mock_result

        runner = ProcessRunner()
        result = runner.execute(["echo", "test"], timeout=60, show_output=True, cwd=Path("/tmp"))

        assert result is True

        # Check that options were passed correctly
        call_args = mock_run_process.call_args
        assert call_args[1]["timeout"] == 60
        assert call_args[1]["capture_output"] is False  # show_output=True means capture_output=False
        assert call_args[1]["cwd"] == Path("/tmp")


class TestProcessManagement:
    """Test process management functions."""

    def test_check_process_running_found(self) -> None:
        """Test checking for running process when found."""
        with patch("builtins.__import__") as mock_import:
            mock_psutil = Mock()
            mock_proc = Mock()
            mock_proc.info = {"name": "notepad.exe"}
            mock_psutil.process_iter.return_value = [mock_proc]

            def import_side_effect(name: str, *args: Any, **kwargs: Any) -> Any:
                if name == "psutil":
                    return mock_psutil
                return __import__(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect

            result = check_process_running("notepad")
            assert result is True

    def test_check_process_running_not_found(self) -> None:
        """Test checking for running process when not found."""
        with patch("builtins.__import__") as mock_import:
            mock_psutil = Mock()
            mock_proc = Mock()
            mock_proc.info = {"name": "other.exe"}
            mock_psutil.process_iter.return_value = [mock_proc]

            def import_side_effect(name: str, *args: Any, **kwargs: Any) -> Any:
                if name == "psutil":
                    return mock_psutil
                return __import__(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect

            result = check_process_running("notepad")
            assert result is False

    def test_check_process_running_psutil_unavailable(self) -> None:
        """Test checking process when psutil raises ImportError."""
        with patch("builtins.__import__") as mock_import:

            def import_side_effect(name: str, *args: Any, **kwargs: Any) -> Any:
                if name == "psutil":
                    raise ImportError("psutil not available")
                return __import__(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect

            result = check_process_running("notepad")
            assert result is False

    def test_check_process_running_exception(self) -> None:
        """Test checking process when exception occurs."""
        with patch("builtins.__import__") as mock_import:
            mock_psutil = Mock()
            mock_psutil.process_iter.side_effect = Exception("Process error")

            def import_side_effect(name: str, *args: Any, **kwargs: Any) -> Any:
                if name == "psutil":
                    return mock_psutil
                return __import__(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect

            # The function should handle the exception and return False
            result = check_process_running("notepad")
            assert result is False

    def test_kill_process_success(self) -> None:
        """Test killing process successfully."""
        with patch("builtins.__import__") as mock_import:
            mock_psutil = Mock()
            mock_proc = Mock()
            mock_proc.info = {"name": "notepad.exe"}
            mock_proc.pid = 1234
            mock_psutil.process_iter.return_value = [mock_proc]

            def import_side_effect(name: str, *args: Any, **kwargs: Any) -> Any:
                if name == "psutil":
                    return mock_psutil
                return __import__(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect

            result = kill_process("notepad")
            assert result is True
            mock_proc.kill.assert_called_once()

    def test_kill_process_not_found(self) -> None:
        """Test killing process when not found."""
        with patch("builtins.__import__") as mock_import:
            mock_psutil = Mock()
            mock_proc = Mock()
            mock_proc.info = {"name": "other.exe"}
            mock_psutil.process_iter.return_value = [mock_proc]

            def import_side_effect(name: str, *args: Any, **kwargs: Any) -> Any:
                if name == "psutil":
                    return mock_psutil
                return __import__(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect

            result = kill_process("notepad")
            assert result is False

    def test_kill_process_psutil_unavailable(self) -> None:
        """Test killing process when psutil unavailable."""
        with patch("builtins.__import__") as mock_import:

            def import_side_effect(name: str, *args: Any, **kwargs: Any) -> Any:
                if name == "psutil":
                    raise ImportError("psutil not available")
                return __import__(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect

            result = kill_process("notepad")
            assert result is False


class TestWindowAutomation:
    """Test window automation functionality."""

    @patch("PrevisLib.utils.process.sys.platform", "linux")
    def test_window_automation_non_windows(self) -> None:
        """Test window automation on non-Windows platform."""
        result = run_with_window_automation(["notepad"], "Notepad")

        assert result.returncode == -1
        assert "not supported" in result.stderr

    @patch("PrevisLib.utils.process.sys.platform", "win32")
    def test_window_automation_pywinauto_unavailable(self) -> None:
        """Test window automation when pywinauto unavailable."""
        with patch("builtins.__import__", side_effect=ImportError):
            result = run_with_window_automation(["notepad"], "Notepad")

            assert result.returncode == -1
            assert "pywinauto not installed" in result.stderr
