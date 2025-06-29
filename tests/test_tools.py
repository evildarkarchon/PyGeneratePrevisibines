"""Tests for tool wrapper classes."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from PrevisLib.models.data_classes import BuildMode, CKPEConfig
from PrevisLib.tools.archive import ArchiveTool, ArchiveWrapper
from PrevisLib.tools.ckpe import CKPEConfigHandler
from PrevisLib.tools.creation_kit import CreationKitWrapper
from PrevisLib.tools.xedit import XEditWrapper


class TestCreationKit:
    """Test Creation Kit wrapper."""

    @pytest.fixture
    def wrapper(self, tmp_path) -> CreationKitWrapper:
        """Create a CreationKit wrapper for testing."""
        ck_path = tmp_path / "CreationKit.exe"
        ck_path.write_text("fake ck")
        return CreationKitWrapper(ck_path, "TestMod.esp", BuildMode.CLEAN, None)

    @pytest.fixture
    def wrapper_with_ckpe(self, tmp_path) -> CreationKitWrapper:
        """Create a test Creation Kit wrapper with CKPE config."""
        ck_path = tmp_path / "CreationKit.exe"
        ck_path.write_text("fake ck")
        ckpe_config = CKPEConfig(handle_setting=True, log_output_file="test.log", config_path=None)
        return CreationKitWrapper(ck_path, "TestMod.esp", BuildMode.CLEAN, ckpe_config)

    def test_initialization(self, tmp_path) -> None:
        """Test Creation Kit wrapper initialization."""
        ck_path = tmp_path / "CreationKit.exe"
        ck_path.write_text("fake ck")

        # Test different build modes
        for mode in [BuildMode.CLEAN, BuildMode.FILTERED, BuildMode.XBOX]:
            wrapper = CreationKitWrapper(ck_path, "TestMod.esp", mode, None)
            assert wrapper.ck_path == ck_path
            assert wrapper.plugin_name == "TestMod.esp"
            assert wrapper.build_mode == mode
            assert wrapper.ckpe_config is None
            assert wrapper.process_runner is not None

    @patch("PrevisLib.tools.creation_kit.ProcessRunner")
    def test_generate_precombined_success(self, mock_runner_class, wrapper, tmp_path) -> None:
        """Test successful precombined mesh generation."""
        mock_runner = Mock()
        mock_runner.execute.return_value = True
        mock_runner_class.return_value = mock_runner
        wrapper.process_runner = mock_runner

        data_path = tmp_path / "Data"

        with patch.object(wrapper, "_check_ck_errors", return_value=False):
            with patch.object(wrapper, "_disable_graphics_dlls") as mock_disable:
                with patch.object(wrapper, "_restore_graphics_dlls") as mock_restore:
                    result = wrapper.generate_precombined(data_path)

        assert result is True
        mock_runner.execute.assert_called_once()
        mock_disable.assert_called_once()
        mock_restore.assert_called_once()

        # Check command arguments
        args = mock_runner.execute.call_args[0][0]
        assert str(wrapper.ck_path) in args
        assert f"-GeneratePrecombined:{wrapper.plugin_name}" in args
        # Default build mode is CLEAN, so should have "clean" and "all"
        assert "clean" in args
        assert "all" in args

    @patch("PrevisLib.tools.creation_kit.ProcessRunner")
    def test_generate_precombined_filtered_mode(self, mock_runner_class, tmp_path) -> None:
        """Test precombined generation in filtered mode."""
        ck_path = tmp_path / "CreationKit.exe"
        ck_path.write_text("fake ck")
        wrapper = CreationKitWrapper(ck_path, "TestMod.esp", BuildMode.FILTERED, None)

        mock_runner = Mock()
        mock_runner.execute.return_value = True
        mock_runner_class.return_value = mock_runner
        wrapper.process_runner = mock_runner

        data_path = tmp_path / "Data"

        with patch.object(wrapper, "_check_ck_errors", return_value=False):
            with patch.object(wrapper, "_disable_graphics_dlls"):
                with patch.object(wrapper, "_restore_graphics_dlls"):
                    result = wrapper.generate_precombined(data_path)

        assert result is True
        args = mock_runner.execute.call_args[0][0]
        # In filtered mode, should have "filtered" and "all"
        assert "filtered" in args
        assert "all" in args

    @patch("PrevisLib.tools.creation_kit.ProcessRunner")
    def test_generate_precombined_xbox_mode(self, mock_runner_class, tmp_path) -> None:
        """Test precombined generation in Xbox mode."""
        ck_path = tmp_path / "CreationKit.exe"
        ck_path.write_text("fake ck")
        wrapper = CreationKitWrapper(ck_path, "TestMod.esp", BuildMode.XBOX, None)

        mock_runner = Mock()
        mock_runner.execute.return_value = True
        mock_runner_class.return_value = mock_runner
        wrapper.process_runner = mock_runner

        data_path = tmp_path / "Data"

        with patch.object(wrapper, "_check_ck_errors", return_value=False):
            result = wrapper.generate_precombined(data_path)

        assert result is True
        args = mock_runner.execute.call_args[0][0]
        # Xbox mode still uses "filtered" and "all" (non-clean mode)
        assert "filtered" in args
        assert "all" in args

    @patch("PrevisLib.tools.creation_kit.ProcessRunner")
    def test_generate_precombined_process_failure(self, mock_runner_class, wrapper, tmp_path) -> None:
        """Test precombined generation when process fails."""
        mock_runner = Mock()
        mock_runner.execute.return_value = False
        mock_runner_class.return_value = mock_runner
        wrapper.process_runner = mock_runner

        data_path = tmp_path / "Data"

        with patch.object(wrapper, "_disable_graphics_dlls"):
            with patch.object(wrapper, "_restore_graphics_dlls") as mock_restore:
                result = wrapper.generate_precombined(data_path)

        assert result is False
        # Should still restore DLLs even on failure
        mock_restore.assert_called_once()

    @patch("PrevisLib.tools.creation_kit.ProcessRunner")
    def test_generate_precombined_with_ck_errors(self, mock_runner_class, wrapper, tmp_path) -> None:
        """Test precombined generation when CK reports errors."""
        mock_runner = Mock()
        mock_runner.execute.return_value = True
        mock_runner_class.return_value = mock_runner
        wrapper.process_runner = mock_runner

        data_path = tmp_path / "Data"

        with patch.object(wrapper, "_check_ck_errors", return_value=True):
            with patch.object(wrapper, "_disable_graphics_dlls"):
                with patch.object(wrapper, "_restore_graphics_dlls"):
                    result = wrapper.generate_precombined(data_path)

        assert result is False

    @patch("PrevisLib.tools.creation_kit.ProcessRunner")
    def test_compress_psg_success(self, mock_runner_class, wrapper, tmp_path) -> None:
        """Test successful PSG compression."""
        mock_runner = Mock()
        mock_runner.execute.return_value = True
        mock_runner_class.return_value = mock_runner
        wrapper.process_runner = mock_runner

        data_path = tmp_path / "Data"

        with patch.object(wrapper, "_check_ck_errors", return_value=False):
            with patch.object(wrapper, "_disable_graphics_dlls"):
                with patch.object(wrapper, "_restore_graphics_dlls"):
                    result = wrapper.compress_psg(data_path)

        assert result is True
        mock_runner.execute.assert_called_once()

        args = mock_runner.execute.call_args[0][0]
        assert f"-CompressPSG:{wrapper.plugin_name}" in args

    @patch("PrevisLib.tools.creation_kit.ProcessRunner")
    def test_build_cdx_success(self, mock_runner_class, wrapper, tmp_path) -> None:
        """Test successful CDX building."""
        mock_runner = Mock()
        mock_runner.execute.return_value = True
        mock_runner_class.return_value = mock_runner
        wrapper.process_runner = mock_runner

        data_path = tmp_path / "Data"

        with patch.object(wrapper, "_check_ck_errors", return_value=False):
            with patch.object(wrapper, "_disable_graphics_dlls"):
                with patch.object(wrapper, "_restore_graphics_dlls"):
                    result = wrapper.build_cdx(data_path)

        assert result is True
        mock_runner.execute.assert_called_once()

        args = mock_runner.execute.call_args[0][0]
        assert f"-BuildCDX:{wrapper.plugin_name}" in args

    @patch("PrevisLib.tools.creation_kit.ProcessRunner")
    def test_generate_previs_data_success(self, mock_runner_class, wrapper, tmp_path) -> None:
        """Test successful previs data generation."""
        mock_runner = Mock()
        mock_runner.execute.return_value = True
        mock_runner_class.return_value = mock_runner
        wrapper.process_runner = mock_runner

        data_path = tmp_path / "Data"

        with patch.object(wrapper, "_check_ck_errors", return_value=False):
            with patch.object(wrapper, "_check_previs_completion", return_value=True):
                with patch.object(wrapper, "_disable_graphics_dlls"):
                    with patch.object(wrapper, "_restore_graphics_dlls"):
                        result = wrapper.generate_previs_data(data_path)

        assert result is True
        mock_runner.execute.assert_called_once()

        # Check timeout (should be 172800 - 2 days)
        call_args = mock_runner.execute.call_args
        assert call_args[1]["timeout"] == 172800

        # Check command arguments
        args = mock_runner.execute.call_args[0][0]
        assert str(wrapper.ck_path) in args
        assert f"-GeneratePreVisData:{wrapper.plugin_name}" in args
        assert "clean" in args
        assert "all" in args

    @patch("PrevisLib.tools.creation_kit.ProcessRunner")
    def test_generate_previs_data_completion_failure(self, mock_runner_class, wrapper, tmp_path) -> None:
        """Test previs data generation when completion check fails."""
        mock_runner = Mock()
        mock_runner.execute.return_value = True
        mock_runner_class.return_value = mock_runner
        wrapper.process_runner = mock_runner

        data_path = tmp_path / "Data"

        with patch.object(wrapper, "_check_ck_errors", return_value=False):
            with patch.object(wrapper, "_check_previs_completion", return_value=False):
                with patch.object(wrapper, "_disable_graphics_dlls"):
                    with patch.object(wrapper, "_restore_graphics_dlls"):
                        result = wrapper.generate_previs_data(data_path)

        assert result is False

    def test_check_ck_errors_multiple_patterns(self, tmp_path) -> None:
        """Test CK error checking with multiple error patterns."""
        ck_path = tmp_path / "CreationKit.exe"
        ck_path.write_text("fake ck")
        data_path = tmp_path / "Data"
        data_path.mkdir()

        # Create log file
        log_dir = data_path.parent / "Logs"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "CreationKit.log"

        # Create CKPE config pointing to the log file
        ckpe_config = CKPEConfig(handle_setting=True, log_output_file=str(log_file), config_path=None)
        wrapper = CreationKitWrapper(ck_path, "TestMod.esp", BuildMode.CLEAN, ckpe_config)

        # Test each error pattern - use exact patterns from implementation
        error_patterns = ["DEFAULT: OUT OF HANDLE ARRAY ENTRIES", "Failed to load", "ERROR:", "FATAL:", "Exception"]

        for pattern in error_patterns:
            log_file.write_text(f"Some content\n{pattern}\nMore content")

            result = wrapper._check_ck_errors(data_path)
            assert result is True

    def test_check_ck_errors_multiple_locations(self, tmp_path) -> None:
        """Test CK error checking in multiple log locations."""
        ck_path = tmp_path / "CreationKit.exe"
        ck_path.write_text("fake ck")
        data_path = tmp_path / "Data"
        data_path.mkdir()

        # Test different log locations
        log_locations = [data_path.parent / "Logs" / "CreationKit.log", data_path / "Logs" / "CreationKit.log"]

        for log_path in log_locations:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text("Some content\nERROR: test error\nMore content")

            # Create CKPE config pointing to this specific log file
            ckpe_config = CKPEConfig(handle_setting=True, log_output_file=str(log_path), config_path=None)
            wrapper = CreationKitWrapper(ck_path, "TestMod.esp", BuildMode.CLEAN, ckpe_config)

            result = wrapper._check_ck_errors(data_path)
            assert result is True

            # Clean up
            log_path.unlink()

    def test_check_ck_errors_file_read_exception(self, tmp_path) -> None:
        """Test CK error checking when file read fails."""
        ck_path = tmp_path / "CreationKit.exe"
        ck_path.write_text("fake ck")
        data_path = tmp_path / "Data"
        data_path.mkdir()

        log_dir = data_path.parent / "Logs"
        log_dir.mkdir()
        log_file = log_dir / "CreationKit.log"
        log_file.write_text("content")

        # Create CKPE config pointing to the log file
        ckpe_config = CKPEConfig(handle_setting=True, log_output_file=str(log_file), config_path=None)
        wrapper = CreationKitWrapper(ck_path, "TestMod.esp", BuildMode.CLEAN, ckpe_config)

        # Mock file read to raise exception
        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            result = wrapper._check_ck_errors(data_path)
            # Should return False when exception occurs
            assert result is False

    def test_check_previs_completion_patterns(self, tmp_path) -> None:
        """Test previs completion checking with different failure patterns."""
        ck_path = tmp_path / "CreationKit.exe"
        ck_path.write_text("fake ck")
        data_path = tmp_path / "Data"
        data_path.mkdir()

        # Create log file
        log_dir = data_path.parent / "Logs"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "CreationKit.log"

        # Create CKPE config pointing to the log file
        ckpe_config = CKPEConfig(handle_setting=True, log_output_file=str(log_file), config_path=None)
        wrapper = CreationKitWrapper(ck_path, "TestMod.esp", BuildMode.CLEAN, ckpe_config)

        # Use the exact failure patterns from the implementation
        failure_patterns = ["ERROR: visibility task did not complete.", "Previs generation failed", "Could not complete previs"]

        for pattern in failure_patterns:
            log_file.write_text(f"Some content\n{pattern}\nMore content")

            result = wrapper._check_previs_completion(data_path)
            assert result is False

        # Test with successful completion (no failure patterns)
        log_file.write_text("Some content\nPrevis generation completed successfully\nMore content")
        result = wrapper._check_previs_completion(data_path)
        assert result is True

    def test_check_previs_completion_success(self, tmp_path) -> None:
        """Test previs completion checking with successful log."""
        ck_path = tmp_path / "CreationKit.exe"
        ck_path.write_text("fake ck")
        data_path = tmp_path / "Data"
        data_path.mkdir()

        log_dir = data_path.parent / "Logs"
        log_dir.mkdir()
        log_file = log_dir / "CreationKit.log"
        log_file.write_text("Some content\nPrevis generation completed\nMore content")

        # Create CKPE config pointing to the log file
        ckpe_config = CKPEConfig(handle_setting=True, log_output_file=str(log_file), config_path=None)
        wrapper = CreationKitWrapper(ck_path, "TestMod.esp", BuildMode.CLEAN, ckpe_config)

        result = wrapper._check_previs_completion(data_path)
        assert result is True

    def test_ckpe_config_log_file(self, tmp_path) -> None:
        """Test error checking with CKPE config log file."""
        ck_path = tmp_path / "CreationKit.exe"
        ck_path.write_text("fake ck")
        data_path = tmp_path / "Data"
        data_path.mkdir()

        # Create CKPE config with custom log path
        log_path = tmp_path / "custom_ck.log"
        ckpe_config = CKPEConfig(handle_setting=True, log_output_file=str(log_path), config_path=None)

        wrapper = CreationKitWrapper(ck_path, "TestMod.esp", BuildMode.CLEAN, ckpe_config)

        # Test with error in custom log - use exact pattern from implementation
        log_path.write_text("Some content\nDEFAULT: OUT OF HANDLE ARRAY ENTRIES\nMore content")
        result = wrapper._check_ck_errors(data_path)
        assert result is True

        # Test with no error in custom log
        log_path.write_text("Some content\nNormal log content\nMore content")
        result = wrapper._check_ck_errors(data_path)
        assert result is False

    def test_ckpe_config_no_log_file(self, tmp_path) -> None:
        """Test error checking with CKPE config but no log file specified."""
        ck_path = tmp_path / "CreationKit.exe"
        ck_path.write_text("fake ck")
        data_path = tmp_path / "Data"
        data_path.mkdir()

        # Create CKPE config without log file
        ckpe_config = CKPEConfig(handle_setting=True, log_output_file="", config_path=None)

        wrapper = CreationKitWrapper(ck_path, "TestMod.esp", BuildMode.CLEAN, ckpe_config)

        # Should skip log checking and return False (no errors)
        result = wrapper._check_ck_errors(data_path)
        assert result is False

        # Should skip completion checking and return True (success)
        result = wrapper._check_previs_completion(data_path)
        assert result is True

    def test_ckpe_config_relative_log_path(self, tmp_path) -> None:
        """Test error checking with relative log path in CKPE config."""
        ck_path = tmp_path / "CreationKit.exe"
        ck_path.write_text("fake ck")
        data_path = tmp_path / "Data"
        data_path.mkdir()

        # Create log file relative to data path
        log_dir = data_path / "Logs"
        log_dir.mkdir()
        log_file = log_dir / "custom.log"

        # CKPE config with relative path
        ckpe_config = CKPEConfig(handle_setting=True, log_output_file="Logs/custom.log", config_path=None)

        wrapper = CreationKitWrapper(ck_path, "TestMod.esp", BuildMode.CLEAN, ckpe_config)

        # Test with error in log
        log_file.write_text("Some content\nFATAL: Critical error\nMore content")
        result = wrapper._check_ck_errors(data_path)
        assert result is True

    def test_dll_management(self, tmp_path) -> None:
        """Test DLL disable/restore functionality."""
        ck_path = tmp_path / "CreationKit.exe"
        ck_path.write_text("fake ck")

        # Create some fake DLL files
        dll_names = ["d3d11.dll", "d3d10.dll", "dxgi.dll"]
        for dll_name in dll_names:
            dll_path = tmp_path / dll_name
            dll_path.write_text("fake dll")

        wrapper = CreationKitWrapper(ck_path, "TestMod.esp", BuildMode.CLEAN, None)

        # Test disable
        wrapper._disable_graphics_dlls()

        # Check that DLLs were renamed
        for dll_name in dll_names:
            original_path = tmp_path / dll_name
            disabled_path = tmp_path / f"{dll_name}-PJMdisabled"
            assert not original_path.exists()
            assert disabled_path.exists()

        # Test restore
        wrapper._restore_graphics_dlls()

        # Check that DLLs were restored
        for dll_name in dll_names:
            original_path = tmp_path / dll_name
            disabled_path = tmp_path / f"{dll_name}-PJMdisabled"
            assert original_path.exists()
            assert not disabled_path.exists()

    def test_dll_management_missing_dlls(self, tmp_path) -> None:
        """Test DLL management when DLLs don't exist."""
        ck_path = tmp_path / "CreationKit.exe"
        ck_path.write_text("fake ck")

        wrapper = CreationKitWrapper(ck_path, "TestMod.esp", BuildMode.CLEAN, None)

        # Should not fail when DLLs don't exist
        wrapper._disable_graphics_dlls()
        wrapper._restore_graphics_dlls()

    def test_check_ck_errors_enhanced_patterns(self, tmp_path) -> None:
        """Test enhanced CK error checking with patterns from batch file."""
        ck_path = tmp_path / "CreationKit.exe"
        ck_path.write_text("fake ck")
        data_path = tmp_path / "Data"
        data_path.mkdir()

        # Create log file
        log_dir = data_path.parent / "Logs"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "CreationKit.log"

        # Create CKPE config pointing to the log file
        ckpe_config = CKPEConfig(handle_setting=True, log_output_file=str(log_file), config_path=None)
        wrapper = CreationKitWrapper(ck_path, "TestMod.esp", BuildMode.CLEAN, ckpe_config)

        # Test enhanced error patterns including exact batch file pattern
        error_patterns = ["DEFAULT: OUT OF HANDLE ARRAY ENTRIES", "Failed to load", "ERROR:", "FATAL:", "Exception"]

        for pattern in error_patterns:
            log_file.write_text(f"Some content\n{pattern}\nMore content")

            result = wrapper._check_ck_errors(data_path)
            assert result is True

    def test_check_previs_completion_enhanced_patterns(self, tmp_path) -> None:
        """Test enhanced previs completion checking with patterns from batch file."""
        ck_path = tmp_path / "CreationKit.exe"
        ck_path.write_text("fake ck")
        data_path = tmp_path / "Data"
        data_path.mkdir()

        # Create log file
        log_dir = data_path.parent / "Logs"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "CreationKit.log"

        # Create CKPE config pointing to the log file
        ckpe_config = CKPEConfig(handle_setting=True, log_output_file=str(log_file), config_path=None)
        wrapper = CreationKitWrapper(ck_path, "TestMod.esp", BuildMode.CLEAN, ckpe_config)

        # Test enhanced failure patterns including exact batch file pattern
        failure_patterns = ["ERROR: visibility task did not complete.", "Previs generation failed", "Could not complete previs"]

        for pattern in failure_patterns:
            log_file.write_text(f"Some content\n{pattern}\nMore content")

            result = wrapper._check_previs_completion(data_path)
            assert result is False


class TestXEdit:
    """Test xEdit wrapper functionality."""

    @pytest.fixture
    def wrapper(self, tmp_path) -> XEditWrapper:
        """Create a test xEdit wrapper."""
        xedit_path = tmp_path / "FO4Edit.exe"
        xedit_path.write_text("fake xedit")
        return XEditWrapper(xedit_path, "TestMod.esp")

    @patch("PrevisLib.tools.xedit.ProcessRunner")
    def test_merge_combined_objects_success(self, mock_runner_class, wrapper, tmp_path) -> None:
        """Test successful combined objects merge."""
        mock_runner = Mock()
        mock_runner.execute.return_value = True
        mock_runner_class.return_value = mock_runner
        wrapper.process_runner = mock_runner

        data_path = tmp_path / "Data"
        script_path = tmp_path / "TestScript.pas"

        with patch("PrevisLib.tools.xedit.PYWINAUTO_AVAILABLE", False):
            with patch.object(wrapper, "_check_xedit_log", return_value=True):
                result = wrapper.merge_combined_objects(data_path, script_path)

        assert result is True
        mock_runner.execute.assert_called_once()

    @patch("PrevisLib.tools.xedit.ProcessRunner")
    def test_merge_combined_objects_process_runner_failure(self, mock_runner_class, wrapper, tmp_path) -> None:
        """Test combined objects merge failure using ProcessRunner."""
        mock_runner = Mock()
        mock_runner.execute.return_value = False
        mock_runner_class.return_value = mock_runner
        wrapper.process_runner = mock_runner

        data_path = tmp_path / "Data"
        script_path = tmp_path / "TestScript.pas"

        with patch("PrevisLib.tools.xedit.PYWINAUTO_AVAILABLE", False):
            result = wrapper.merge_combined_objects(data_path, script_path)

        assert result is False

    @patch("PrevisLib.tools.xedit.XEditWrapper._run_with_automation", return_value=True)
    def test_merge_combined_objects_with_automation_success(self, mock_run_auto, wrapper, tmp_path) -> None:
        """Test successful combined objects merge with pywinauto."""
        data_path = tmp_path / "Data"
        script_path = tmp_path / "TestScript.pas"

        with patch("PrevisLib.tools.xedit.PYWINAUTO_AVAILABLE", True):
            with patch.object(wrapper, "_check_xedit_log", return_value=True):
                result = wrapper.merge_combined_objects(data_path, script_path)

        assert result is True
        mock_run_auto.assert_called_once()

    @patch("PrevisLib.tools.xedit.XEditWrapper._run_with_automation", return_value=False)
    def test_merge_combined_objects_with_automation_failure(self, mock_run_auto, wrapper, tmp_path) -> None:
        """Test failing combined objects merge with pywinauto."""
        data_path = tmp_path / "Data"
        script_path = tmp_path / "TestScript.pas"

        with patch("PrevisLib.tools.xedit.PYWINAUTO_AVAILABLE", True):
            result = wrapper.merge_combined_objects(data_path, script_path)

        assert result is False
        mock_run_auto.assert_called_once()

    @patch("PrevisLib.tools.xedit.ProcessRunner")
    def test_merge_previs_success(self, mock_runner_class, wrapper, tmp_path) -> None:
        """Test successful previs merge."""
        mock_runner = Mock()
        mock_runner.execute.return_value = True
        mock_runner_class.return_value = mock_runner
        wrapper.process_runner = mock_runner

        data_path = tmp_path / "Data"
        script_path = tmp_path / "TestScript.pas"

        with patch("PrevisLib.tools.xedit.PYWINAUTO_AVAILABLE", False):
            with patch.object(wrapper, "_check_xedit_log", return_value=True):
                result = wrapper.merge_previs(data_path, script_path)

        assert result is True
        mock_runner.execute.assert_called_once()

    def test_check_xedit_log_no_log_found(self, wrapper) -> None:
        """Test xEdit log check when no log file is found."""
        with patch.object(Path, "exists", return_value=False):
            # Should return True with a warning
            result = wrapper._check_xedit_log("test operation")
        assert result is True

    def test_check_xedit_log_read_error(self, wrapper, tmp_path) -> None:
        """Test xEdit log check when reading the log file fails."""
        log_path = tmp_path / "UnattendedScript.log"
        log_path.touch()

        with patch("os.environ.get", return_value=str(tmp_path)):
            with patch("PrevisLib.tools.xedit.Path.open", side_effect=OSError("Read error")):
                # Should warn and assume success
                result = wrapper._check_xedit_log("test operation")
        assert result is True

    def test_check_xedit_log_no_completion_indicator(self, wrapper, tmp_path) -> None:
        """Test xEdit log check when log exists but lacks a completion indicator."""
        unattended_log = tmp_path / "UnattendedScript.log"
        unattended_log.write_text("Some random content without completion marker.")

        with patch("os.environ.get", return_value=str(tmp_path)):
            result = wrapper._check_xedit_log("test operation")
        assert result is False

    @patch("subprocess.Popen")
    def test_run_with_automation_success(self, mock_popen, wrapper) -> None:
        """Test the happy path for _run_with_automation."""
        mock_process = Mock()
        mock_process.pid = 1234
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process

        mock_app = Mock()
        mock_main_window = Mock()
        mock_main_window.exists.return_value = True
        mock_main_window.descendants.return_value = []
        mock_app.window.return_value = mock_main_window

        with patch("PrevisLib.tools.xedit.PYWINAUTO_AVAILABLE", True):
            with patch("PrevisLib.tools.xedit.Application") as mock_pywin_app:
                mock_pywin_app.return_value.connect.return_value = mock_app
                with patch.object(wrapper, "_is_xedit_busy", return_value=False):
                    result = wrapper._run_with_automation([], "test op")

        assert result is True
        mock_popen.assert_called_once()
        mock_main_window.close.assert_called_once()

    @patch("subprocess.Popen")
    def test_run_with_automation_error_dialog(self, mock_popen, wrapper) -> None:
        """Test _run_with_automation when an error dialog appears."""
        mock_process = Mock()
        mock_process.pid = 1234
        mock_popen.return_value = mock_process

        mock_app = Mock()
        mock_main_window = Mock()
        mock_main_window.exists.return_value = True
        mock_error_dialog = Mock()
        mock_error_dialog.window_text.return_value = "An error occurred"
        mock_main_window.descendants.return_value = [mock_error_dialog]
        mock_app.window.return_value = mock_main_window

        with patch("PrevisLib.tools.xedit.PYWINAUTO_AVAILABLE", True):
            with patch("PrevisLib.tools.xedit.Application") as mock_pywin_app:
                mock_pywin_app.return_value.connect.return_value = mock_app
                result = wrapper._run_with_automation([], "test op")

        assert result is False
        mock_error_dialog.close.assert_called_once()

    def test_is_xedit_busy(self, wrapper) -> None:
        """Test the _is_xedit_busy helper function."""
        mock_window = Mock()
        mock_status_bar = Mock()
        mock_status_bar.exists.return_value = True
        mock_window.child_window.return_value = mock_status_bar

        # Test when busy
        mock_status_bar.window_text.return_value = "Processing... please wait."
        assert wrapper._is_xedit_busy(mock_window) is True

        # Test when not busy
        mock_status_bar.window_text.return_value = "Ready."
        assert wrapper._is_xedit_busy(mock_window) is False

        # Test when status bar doesn't exist
        mock_status_bar.exists.return_value = False
        assert wrapper._is_xedit_busy(mock_window) is False

    def test_check_xedit_log_enhanced_patterns(self, tmp_path) -> None:
        """Test enhanced xEdit log checking with patterns from batch file."""
        xedit_path = tmp_path / "FO4Edit.exe"
        xedit_path.write_text("fake xedit")
        wrapper = XEditWrapper(xedit_path, "TestMod.esp")

        data_path = tmp_path / "Data"

        # Create a temporary unattended log file
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            unattended_log = temp_path / "UnattendedScript.log"

            with patch("os.environ.get", return_value=str(temp_path)):
                # Test exact error pattern from batch file
                unattended_log.write_text("Some content\nError: Test error\nMore content")
                result = wrapper._check_xedit_log("test operation")
                assert result is False

                # Test exact success pattern from batch file
                unattended_log.write_text("Some content\nCompleted: No Errors.\nMore content")
                result = wrapper._check_xedit_log("test operation")
                assert result is True

                # Test general completion pattern from batch file
                unattended_log.write_text("Some content\nCompleted: \nMore content")
                result = wrapper._check_xedit_log("test operation")
                assert result is True

                # Test missing completion indicator
                unattended_log.write_text("Some content\nNo completion indicator\nMore content")
                result = wrapper._check_xedit_log("test operation")
                assert result is False


class TestCKPEConfigHandler:
    """Test CKPE configuration handler."""

    @pytest.fixture
    def handler(self, tmp_path) -> CKPEConfigHandler:
        """Create a CKPEConfigHandler for testing."""
        return CKPEConfigHandler(tmp_path)

    def test_load_config_no_files(self, handler, tmp_path) -> None:
        """Test loading config when no config files exist."""
        (tmp_path / "Data").mkdir()
        result = handler.load_config("TestPlugin")
        assert result is None

    @patch("PrevisLib.tools.ckpe.CKPEConfig")
    def test_load_toml_config_success(self, mock_ckpe_config, handler, tmp_path) -> None:
        """Test loading a valid TOML config file."""
        data_path = tmp_path / "Data"
        data_path.mkdir()
        toml_path = data_path / "TestPlugin_CKPEConfig.toml"
        toml_path.touch()

        mock_config = Mock(spec=CKPEConfig)
        mock_ckpe_config.from_toml.return_value = mock_config

        result = handler.load_config("TestPlugin")

        assert result == mock_config
        mock_ckpe_config.from_toml.assert_called_once_with(toml_path)

    @patch("PrevisLib.tools.ckpe.CKPEConfig")
    def test_load_ini_config_success(self, mock_ckpe_config, handler, tmp_path) -> None:
        """Test loading a valid INI config file when TOML is absent."""
        data_path = tmp_path / "Data"
        data_path.mkdir()
        ini_path = data_path / "TestPlugin_CKPEConfig.ini"
        ini_path.touch()

        mock_config = Mock(spec=CKPEConfig)
        mock_ckpe_config.from_ini.return_value = mock_config

        result = handler.load_config("TestPlugin")

        assert result == mock_config
        mock_ckpe_config.from_ini.assert_called_once_with(ini_path)
        mock_ckpe_config.from_toml.assert_not_called()

    @patch("PrevisLib.tools.ckpe.CKPEConfig")
    def test_load_prefers_toml_over_ini(self, mock_ckpe_config, handler, tmp_path) -> None:
        """Test that TOML config is preferred when both TOML and INI exist."""
        data_path = tmp_path / "Data"
        data_path.mkdir()
        toml_path = data_path / "TestPlugin_CKPEConfig.toml"
        toml_path.touch()
        ini_path = data_path / "TestPlugin_CKPEConfig.ini"
        ini_path.touch()

        mock_toml_config = Mock(spec=CKPEConfig)
        mock_ckpe_config.from_toml.return_value = mock_toml_config

        result = handler.load_config("TestPlugin")

        assert result == mock_toml_config
        mock_ckpe_config.from_toml.assert_called_once_with(toml_path)
        mock_ckpe_config.from_ini.assert_not_called()

    @patch("PrevisLib.tools.ckpe.CKPEConfig")
    def test_load_falls_back_to_ini_on_toml_error(self, mock_ckpe_config, handler, tmp_path) -> None:
        """Test fallback to INI when TOML loading fails."""
        data_path = tmp_path / "Data"
        data_path.mkdir()
        toml_path = data_path / "TestPlugin_CKPEConfig.toml"
        toml_path.touch()
        ini_path = data_path / "TestPlugin_CKPEConfig.ini"
        ini_path.touch()

        mock_ckpe_config.from_toml.side_effect = ValueError("Invalid TOML")
        mock_ini_config = Mock(spec=CKPEConfig)
        mock_ckpe_config.from_ini.return_value = mock_ini_config

        result = handler.load_config("TestPlugin")

        assert result == mock_ini_config
        mock_ckpe_config.from_toml.assert_called_once_with(toml_path)
        mock_ckpe_config.from_ini.assert_called_once_with(ini_path)

    @patch("PrevisLib.tools.ckpe.CKPEConfig")
    def test_load_returns_none_on_all_errors(self, mock_ckpe_config, handler, tmp_path) -> None:
        """Test that None is returned if both TOML and INI loading fail."""
        data_path = tmp_path / "Data"
        data_path.mkdir()
        toml_path = data_path / "TestPlugin_CKPEConfig.toml"
        toml_path.touch()
        ini_path = data_path / "TestPlugin_CKPEConfig.ini"
        ini_path.touch()

        mock_ckpe_config.from_toml.side_effect = ValueError("Invalid TOML")
        mock_ckpe_config.from_ini.side_effect = ValueError("Invalid INI")

        result = handler.load_config("TestPlugin")

        assert result is None
        mock_ckpe_config.from_toml.assert_called_once_with(toml_path)
        mock_ckpe_config.from_ini.assert_called_once_with(ini_path)


class TestArchiveWrapper:
    """Test Archive wrapper functionality."""

    @pytest.fixture
    def archive2_wrapper(self, tmp_path) -> ArchiveWrapper:
        """Create an Archive2 wrapper for testing."""
        archive_path = tmp_path / "Archive2.exe"
        archive_path.write_text("fake archive2")
        return ArchiveWrapper(ArchiveTool.ARCHIVE2, archive_path, BuildMode.CLEAN)

    @pytest.fixture
    def archive2_wrapper_xbox(self, tmp_path) -> ArchiveWrapper:
        """Create an Archive2 wrapper with Xbox build mode for testing."""
        archive_path = tmp_path / "Archive2.exe"
        archive_path.write_text("fake archive2")
        return ArchiveWrapper(ArchiveTool.ARCHIVE2, archive_path, BuildMode.XBOX)

    @pytest.fixture
    def bsarch_wrapper(self, tmp_path) -> ArchiveWrapper:
        """Create a BSArch wrapper for testing."""
        bsarch_path = tmp_path / "BSArch.exe"
        bsarch_path.write_text("fake bsarch")
        return ArchiveWrapper(ArchiveTool.BSARCH, bsarch_path, BuildMode.CLEAN)

    def test_initialization(self, tmp_path) -> None:
        """Test ArchiveWrapper initialization with different build modes."""
        archive_path = tmp_path / "Archive2.exe"
        archive_path.write_text("fake archive2")

        # Test different build modes
        for mode in [BuildMode.CLEAN, BuildMode.FILTERED, BuildMode.XBOX]:
            wrapper = ArchiveWrapper(ArchiveTool.ARCHIVE2, archive_path, mode)
            assert wrapper.tool == ArchiveTool.ARCHIVE2
            assert wrapper.tool_path == archive_path
            assert wrapper.build_mode == mode
            assert wrapper.process_runner is not None

    @patch("PrevisLib.tools.archive.ProcessRunner")
    def test_create_archive2_default_compression(self, mock_runner_class, archive2_wrapper, tmp_path) -> None:
        """Test Archive2 archive creation with default compression."""
        mock_runner = Mock()
        mock_runner.execute.return_value = True
        mock_runner_class.return_value = mock_runner
        archive2_wrapper.process_runner = mock_runner

        archive_path = tmp_path / "test.ba2"
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        # Mock archive file creation
        with patch.object(Path, "exists", return_value=True):
            result = archive2_wrapper.create_archive(archive_path, source_dir, compress=True)

        assert result is True
        mock_runner.execute.assert_called_once()

        # Check command arguments
        args = mock_runner.execute.call_args[0][0]
        assert str(archive2_wrapper.tool_path) in args
        assert f"-create={archive_path}" in args
        assert f"-root={source_dir}" in args
        assert "-compression=Default" in args

    @patch("PrevisLib.tools.archive.ProcessRunner")
    def test_create_archive2_xbox_compression(self, mock_runner_class, archive2_wrapper_xbox, tmp_path) -> None:
        """Test Archive2 archive creation with Xbox compression mode."""
        mock_runner = Mock()
        mock_runner.execute.return_value = True
        mock_runner_class.return_value = mock_runner
        archive2_wrapper_xbox.process_runner = mock_runner

        archive_path = tmp_path / "test.ba2"
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        # Mock archive file creation
        with patch.object(Path, "exists", return_value=True):
            result = archive2_wrapper_xbox.create_archive(archive_path, source_dir, compress=True)

        assert result is True
        mock_runner.execute.assert_called_once()

        # Check command arguments for Xbox compression
        args = mock_runner.execute.call_args[0][0]
        assert str(archive2_wrapper_xbox.tool_path) in args
        assert f"-create={archive_path}" in args
        assert f"-root={source_dir}" in args
        assert "-compression=XBox" in args

    @patch("PrevisLib.tools.archive.ProcessRunner")
    def test_create_archive2_no_compression(self, mock_runner_class, archive2_wrapper, tmp_path) -> None:
        """Test Archive2 archive creation with no compression."""
        mock_runner = Mock()
        mock_runner.execute.return_value = True
        mock_runner_class.return_value = mock_runner
        archive2_wrapper.process_runner = mock_runner

        archive_path = tmp_path / "test.ba2"
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        # Mock archive file creation
        with patch.object(Path, "exists", return_value=True):
            result = archive2_wrapper.create_archive(archive_path, source_dir, compress=False)

        assert result is True
        mock_runner.execute.assert_called_once()

        # Check command arguments
        args = mock_runner.execute.call_args[0][0]
        assert "-compression=None" in args

    @patch("PrevisLib.tools.archive.ProcessRunner")
    def test_create_archive2_with_file_list(self, mock_runner_class, archive2_wrapper, tmp_path) -> None:
        """Test Archive2 archive creation with specific file list."""
        mock_runner = Mock()
        mock_runner.execute.return_value = True
        mock_runner_class.return_value = mock_runner
        archive2_wrapper.process_runner = mock_runner

        archive_path = tmp_path / "test.ba2"
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        file_list = ["file1.nif", "file2.nif"]

        # Mock archive file creation
        with patch.object(Path, "exists", return_value=True):
            result = archive2_wrapper.create_archive(archive_path, source_dir, file_list=file_list, compress=True)

        assert result is True
        mock_runner.execute.assert_called_once()

        # Check that sourceFile argument was used
        args = mock_runner.execute.call_args[0][0]
        source_file_arg = [arg for arg in args if arg.startswith("-sourceFile=")]
        assert len(source_file_arg) == 1

    @patch("PrevisLib.tools.archive.ProcessRunner")
    def test_create_bsarch_archive(self, mock_runner_class, bsarch_wrapper, tmp_path) -> None:
        """Test BSArch archive creation."""
        mock_runner = Mock()
        mock_runner.execute.return_value = True
        mock_runner_class.return_value = mock_runner
        bsarch_wrapper.process_runner = mock_runner

        archive_path = tmp_path / "test.ba2"
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        # Mock archive file creation
        with patch.object(Path, "exists", return_value=True):
            result = bsarch_wrapper.create_archive(archive_path, source_dir, compress=True)

        assert result is True
        mock_runner.execute.assert_called_once()

        # Check command arguments
        args = mock_runner.execute.call_args[0][0]
        assert str(bsarch_wrapper.tool_path) in args
        assert "pack" in args
        assert str(source_dir) in args
        assert str(archive_path) in args
        assert "-z" in args
        assert "1" in args  # Compression enabled
        assert "-fo4" in args

    @patch("PrevisLib.tools.archive.ProcessRunner")
    def test_extract_archive2(self, mock_runner_class, archive2_wrapper, tmp_path) -> None:
        """Test Archive2 archive extraction."""
        mock_runner = Mock()
        mock_runner.execute.return_value = True
        mock_runner_class.return_value = mock_runner
        archive2_wrapper.process_runner = mock_runner

        archive_path = tmp_path / "test.ba2"
        archive_path.write_text("fake archive")
        output_dir = tmp_path / "output"

        result = archive2_wrapper.extract_archive(archive_path, output_dir)

        assert result is True
        mock_runner.execute.assert_called_once()

        # Check command arguments
        args = mock_runner.execute.call_args[0][0]
        assert str(archive2_wrapper.tool_path) in args
        assert str(archive_path) in args
        assert f"-extract={output_dir}" in args

    @patch("PrevisLib.tools.archive.ProcessRunner")
    def test_extract_bsarch(self, mock_runner_class, bsarch_wrapper, tmp_path) -> None:
        """Test BSArch archive extraction."""
        mock_runner = Mock()
        mock_runner.execute.return_value = True
        mock_runner_class.return_value = mock_runner
        bsarch_wrapper.process_runner = mock_runner

        archive_path = tmp_path / "test.ba2"
        archive_path.write_text("fake archive")
        output_dir = tmp_path / "output"

        result = bsarch_wrapper.extract_archive(archive_path, output_dir)

        assert result is True
        mock_runner.execute.assert_called_once()

        # Check command arguments
        args = mock_runner.execute.call_args[0][0]
        assert str(bsarch_wrapper.tool_path) in args
        assert "unpack" in args
        assert str(archive_path) in args
        assert str(output_dir) in args

    def test_extract_nonexistent_archive(self, archive2_wrapper, tmp_path) -> None:
        """Test extraction of non-existent archive."""
        archive_path = tmp_path / "nonexistent.ba2"
        output_dir = tmp_path / "output"

        result = archive2_wrapper.extract_archive(archive_path, output_dir)

        assert result is False

    @patch("PrevisLib.tools.archive.ProcessRunner")
    @patch("PrevisLib.tools.archive.shutil")
    def test_add_to_archive_success(self, mock_shutil, mock_runner_class, archive2_wrapper, tmp_path) -> None:
        """Test adding files to existing archive."""
        # Setup mocks
        mock_runner = Mock()
        mock_runner.execute.return_value = True
        mock_runner_class.return_value = mock_runner
        archive2_wrapper.process_runner = mock_runner

        # Create test files
        archive_path = tmp_path / "test.ba2"
        archive_path.write_text("fake archive")

        files_to_add = [tmp_path / "file1.txt", tmp_path / "file2.txt"]
        for file_path in files_to_add:
            file_path.write_text("test content")

        base_dir = tmp_path

        # Mock the extract and create operations
        with patch.object(archive2_wrapper, "extract_archive", return_value=True):
            with patch.object(archive2_wrapper, "create_archive", return_value=True):
                with patch.object(Path, "exists", return_value=True):
                    result = archive2_wrapper.add_to_archive(archive_path, files_to_add, base_dir)

        assert result is True

    @patch("PrevisLib.tools.archive.ProcessRunner")
    def test_create_archive_process_failure(self, mock_runner_class, archive2_wrapper, tmp_path) -> None:
        """Test archive creation when process fails."""
        mock_runner = Mock()
        mock_runner.execute.return_value = False
        mock_runner_class.return_value = mock_runner
        archive2_wrapper.process_runner = mock_runner

        archive_path = tmp_path / "test.ba2"
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        result = archive2_wrapper.create_archive(archive_path, source_dir, compress=True)

        assert result is False

    @patch("PrevisLib.tools.archive.ProcessRunner")
    def test_create_archive2_creation_fails_despite_process_success(self, mock_runner_class, archive2_wrapper, tmp_path) -> None:
        """Test archive creation failure when file not found after supposedly successful process run."""
        mock_runner = Mock()
        mock_runner.execute.return_value = True
        mock_runner_class.return_value = mock_runner
        archive2_wrapper.process_runner = mock_runner

        archive_path = tmp_path / "test.ba2"
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        # Mock archive file not being created
        with patch.object(Path, "exists", return_value=False):
            result = archive2_wrapper.create_archive(archive_path, source_dir, compress=True)

        assert result is False

    @patch("PrevisLib.tools.archive.ProcessRunner")
    def test_create_bsarch_creation_fails_despite_process_success(self, mock_runner_class, bsarch_wrapper, tmp_path) -> None:
        """Test BSArch creation failure when file not found after supposedly successful process run."""
        mock_runner = Mock()
        mock_runner.execute.return_value = True
        mock_runner_class.return_value = mock_runner
        bsarch_wrapper.process_runner = mock_runner

        archive_path = tmp_path / "test.ba2"
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        # Mock archive file not being created
        with patch.object(Path, "exists", return_value=False):
            result = bsarch_wrapper.create_archive(archive_path, source_dir, compress=True)

        assert result is False

    @patch("PrevisLib.tools.archive.ProcessRunner")
    @patch("PrevisLib.tools.archive.shutil")
    def test_create_bsarch_with_file_list(self, mock_shutil, mock_runner_class, bsarch_wrapper, tmp_path) -> None:
        """Test BSArch archive creation with a specific file list."""
        mock_runner = Mock()
        mock_runner.execute.return_value = True
        mock_runner_class.return_value = mock_runner
        bsarch_wrapper.process_runner = mock_runner

        archive_path = tmp_path / "test.ba2"
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "file1.nif").touch()
        (source_dir / "file2.nif").touch()

        file_list = ["file1.nif", "file2.nif"]

        with patch.object(Path, "exists", return_value=True):
            result = bsarch_wrapper.create_archive(archive_path, source_dir, file_list=file_list, compress=True)

        assert result is True
        mock_runner.execute.assert_called_once()
        # Ensure temp directory was created for file list
        assert mock_shutil.rmtree.call_count == 1

    @patch("PrevisLib.tools.archive.shutil")
    def test_add_to_archive_extraction_fails(self, mock_shutil, archive2_wrapper, tmp_path) -> None:
        """Test add_to_archive when the initial extraction fails."""
        archive_path = tmp_path / "test.ba2"
        files_to_add = [tmp_path / "file1.txt"]
        base_dir = tmp_path

        # Ensure the temp directory exists so cleanup can be tested
        temp_dir = archive_path.parent / f"{archive_path.stem}_temp"
        temp_dir.mkdir()

        with patch.object(archive2_wrapper, "extract_archive", return_value=False):
            result = archive2_wrapper.add_to_archive(archive_path, files_to_add, base_dir)

        assert result is False
        mock_shutil.rmtree.assert_called_once()  # Ensure cleanup is still called

    @patch("PrevisLib.tools.archive.shutil")
    def test_add_to_archive_recreation_fails(self, mock_shutil, archive2_wrapper, tmp_path) -> None:
        """Test add_to_archive when the final recreation fails."""
        archive_path = tmp_path / "test.ba2"
        file_to_add = tmp_path / "file1.txt"
        file_to_add.touch()
        base_dir = tmp_path

        with patch.object(archive2_wrapper, "extract_archive", return_value=True):
            with patch.object(archive2_wrapper, "create_archive", return_value=False):
                result = archive2_wrapper.add_to_archive(archive_path, [file_to_add], base_dir)

        assert result is False
        mock_shutil.rmtree.assert_called_once()  # Ensure cleanup is still called

    @patch("PrevisLib.tools.archive.shutil")
    def test_add_to_archive_with_nonexistent_source_file(self, mock_shutil, archive2_wrapper, tmp_path) -> None:
        """Test add_to_archive when a file to add does not exist."""
        archive_path = tmp_path / "test.ba2"
        non_existent_file = tmp_path / "nonexistent.txt"
        base_dir = tmp_path

        with patch.object(archive2_wrapper, "extract_archive", return_value=True):
            with patch.object(archive2_wrapper, "create_archive", return_value=True):
                result = archive2_wrapper.add_to_archive(archive_path, [non_existent_file], base_dir)

        assert result is True  # Should still succeed
        mock_shutil.copy2.assert_not_called()  # But should not copy the file

    @patch("PrevisLib.tools.archive.ProcessRunner")
    def test_extract_archive2_process_failure(self, mock_runner_class, archive2_wrapper, tmp_path) -> None:
        """Test Archive2 extraction when the process fails."""
        mock_runner = Mock()
        mock_runner.execute.return_value = False
        mock_runner_class.return_value = mock_runner
        archive2_wrapper.process_runner = mock_runner

        archive_path = tmp_path / "test.ba2"
        archive_path.touch()
        output_dir = tmp_path / "output"

        result = archive2_wrapper.extract_archive(archive_path, output_dir)
        assert result is False

    @patch("PrevisLib.tools.archive.ProcessRunner")
    def test_extract_bsarch_process_failure(self, mock_runner_class, bsarch_wrapper, tmp_path) -> None:
        """Test BSArch extraction when the process fails."""
        mock_runner = Mock()
        mock_runner.execute.return_value = False
        mock_runner_class.return_value = mock_runner
        bsarch_wrapper.process_runner = mock_runner

        archive_path = tmp_path / "test.ba2"
        archive_path.touch()
        output_dir = tmp_path / "output"

        result = bsarch_wrapper.extract_archive(archive_path, output_dir)
        assert result is False

    def test_build_mode_inheritance(self, tmp_path) -> None:
        """Test that build mode is properly inherited and accessible."""
        archive_path = tmp_path / "Archive2.exe"
        archive_path.write_text("fake archive2")

        # Test each build mode
        for mode in [BuildMode.CLEAN, BuildMode.FILTERED, BuildMode.XBOX]:
            wrapper = ArchiveWrapper(ArchiveTool.ARCHIVE2, archive_path, mode)
            assert wrapper.build_mode == mode

    @patch("PrevisLib.tools.archive.ProcessRunner")
    def test_compression_mode_combinations(self, mock_runner_class, tmp_path) -> None:
        """Test all combinations of build modes and compression settings."""
        archive_path = tmp_path / "Archive2.exe"
        archive_path.write_text("fake archive2")

        test_archive = tmp_path / "test.ba2"
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        # Test combinations
        test_cases = [
            (BuildMode.CLEAN, True, "-compression=Default"),
            (BuildMode.CLEAN, False, "-compression=None"),
            (BuildMode.FILTERED, True, "-compression=Default"),
            (BuildMode.FILTERED, False, "-compression=None"),
            (BuildMode.XBOX, True, "-compression=XBox"),
            (BuildMode.XBOX, False, "-compression=None"),
        ]

        for build_mode, compress, expected_compression in test_cases:
            mock_runner = Mock()
            mock_runner.execute.return_value = True
            mock_runner_class.return_value = mock_runner

            wrapper = ArchiveWrapper(ArchiveTool.ARCHIVE2, archive_path, build_mode)
            wrapper.process_runner = mock_runner

            # Mock archive file creation
            with patch.object(Path, "exists", return_value=True):
                result = wrapper.create_archive(test_archive, source_dir, compress=compress)

            assert result is True
            args = mock_runner.execute.call_args[0][0]
            assert expected_compression in args
