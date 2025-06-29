"""Tests for tool wrapper classes."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from PrevisLib.models.data_classes import BuildMode, CKPEConfig
from PrevisLib.tools.archive import ArchiveTool, ArchiveWrapper
from PrevisLib.tools.creation_kit import CreationKitWrapper
from PrevisLib.tools.xedit import XEditWrapper


class TestCreationKit:
    """Test Creation Kit wrapper."""

    @pytest.fixture
    def wrapper(self, tmp_path):
        """Create a CreationKit wrapper for testing."""
        ck_path = tmp_path / "CreationKit.exe"
        ck_path.write_text("fake ck")
        return CreationKitWrapper(ck_path, "TestMod.esp", BuildMode.CLEAN, None)

    @pytest.fixture
    def wrapper_with_ckpe(self, tmp_path):
        """Create a test Creation Kit wrapper with CKPE config."""
        ck_path = tmp_path / "CreationKit.exe"
        ck_path.write_text("fake ck")
        ckpe_config = CKPEConfig(handle_setting=True, log_output_file="test.log", config_path=None)
        return CreationKitWrapper(ck_path, "TestMod.esp", BuildMode.CLEAN, ckpe_config)

    def test_initialization(self, tmp_path):
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
    def test_generate_precombined_success(self, mock_runner_class, wrapper, tmp_path):
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
    def test_generate_precombined_filtered_mode(self, mock_runner_class, tmp_path):
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
    def test_generate_precombined_xbox_mode(self, mock_runner_class, tmp_path):
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
    def test_generate_precombined_process_failure(self, mock_runner_class, wrapper, tmp_path):
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
    def test_generate_precombined_with_ck_errors(self, mock_runner_class, wrapper, tmp_path):
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
    def test_compress_psg_success(self, mock_runner_class, wrapper, tmp_path):
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
    def test_build_cdx_success(self, mock_runner_class, wrapper, tmp_path):
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
    def test_generate_previs_data_success(self, mock_runner_class, wrapper, tmp_path):
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
    def test_generate_previs_data_completion_failure(self, mock_runner_class, wrapper, tmp_path):
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

    def test_check_ck_errors_multiple_patterns(self, tmp_path):
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

    def test_check_ck_errors_multiple_locations(self, tmp_path):
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

    def test_check_ck_errors_file_read_exception(self, tmp_path):
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

    def test_check_previs_completion_patterns(self, tmp_path):
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

    def test_check_previs_completion_success(self, tmp_path):
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

    def test_ckpe_config_log_file(self, tmp_path):
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

    def test_ckpe_config_no_log_file(self, tmp_path):
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

    def test_ckpe_config_relative_log_path(self, tmp_path):
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

    def test_dll_management(self, tmp_path):
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

    def test_dll_management_missing_dlls(self, tmp_path):
        """Test DLL management when DLLs don't exist."""
        ck_path = tmp_path / "CreationKit.exe"
        ck_path.write_text("fake ck")

        wrapper = CreationKitWrapper(ck_path, "TestMod.esp", BuildMode.CLEAN, None)

        # Should not fail when DLLs don't exist
        wrapper._disable_graphics_dlls()
        wrapper._restore_graphics_dlls()

    def test_check_ck_errors_enhanced_patterns(self, tmp_path):
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

    def test_check_previs_completion_enhanced_patterns(self, tmp_path):
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
    def wrapper(self, tmp_path):
        """Create a test xEdit wrapper."""
        xedit_path = tmp_path / "FO4Edit.exe"
        xedit_path.write_text("fake xedit")
        return XEditWrapper(xedit_path, "TestMod.esp")

    @patch("PrevisLib.tools.xedit.ProcessRunner")
    def test_merge_combined_objects_success(self, mock_runner_class, wrapper, tmp_path):
        """Test successful combined objects merge."""
        mock_runner = Mock()
        mock_runner.execute.return_value = True
        mock_runner_class.return_value = mock_runner
        wrapper.process_runner = mock_runner

        data_path = tmp_path / "Data"
        script_path = tmp_path / "TestScript.pas"

        # Force use of ProcessRunner instead of automation to avoid platform issues
        with patch("PrevisLib.tools.xedit.PYWINAUTO_AVAILABLE", False):
            with patch.object(wrapper, "_check_xedit_log", return_value=True):
                result = wrapper.merge_combined_objects(data_path, script_path)

        assert result is True
        mock_runner.execute.assert_called_once()

    @patch("PrevisLib.tools.xedit.ProcessRunner")
    def test_merge_previs_success(self, mock_runner_class, wrapper, tmp_path):
        """Test successful previs merge."""
        mock_runner = Mock()
        mock_runner.execute.return_value = True
        mock_runner_class.return_value = mock_runner
        wrapper.process_runner = mock_runner

        data_path = tmp_path / "Data"
        script_path = tmp_path / "TestScript.pas"

        # Force use of ProcessRunner instead of automation to avoid platform issues
        with patch("PrevisLib.tools.xedit.PYWINAUTO_AVAILABLE", False):
            with patch.object(wrapper, "_check_xedit_log", return_value=True):
                result = wrapper.merge_previs(data_path, script_path)

        assert result is True

    def test_check_xedit_log_enhanced_patterns(self, tmp_path):
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
                result = wrapper._check_xedit_log(data_path, "test operation")
                assert result is False

                # Test exact success pattern from batch file
                unattended_log.write_text("Some content\nCompleted: No Errors.\nMore content")
                result = wrapper._check_xedit_log(data_path, "test operation")
                assert result is True

                # Test general completion pattern from batch file
                unattended_log.write_text("Some content\nCompleted: \nMore content")
                result = wrapper._check_xedit_log(data_path, "test operation")
                assert result is True

                # Test missing completion indicator
                unattended_log.write_text("Some content\nNo completion indicator\nMore content")
                result = wrapper._check_xedit_log(data_path, "test operation")
                assert result is False


class TestArchiveWrapper:
    """Test Archive wrapper functionality."""

    @pytest.fixture
    def archive2_wrapper(self, tmp_path):
        """Create an Archive2 wrapper for testing."""
        archive_path = tmp_path / "Archive2.exe"
        archive_path.write_text("fake archive2")
        return ArchiveWrapper(ArchiveTool.ARCHIVE2, archive_path, BuildMode.CLEAN)

    @pytest.fixture
    def archive2_wrapper_xbox(self, tmp_path):
        """Create an Archive2 wrapper with Xbox build mode for testing."""
        archive_path = tmp_path / "Archive2.exe"
        archive_path.write_text("fake archive2")
        return ArchiveWrapper(ArchiveTool.ARCHIVE2, archive_path, BuildMode.XBOX)

    @pytest.fixture
    def bsarch_wrapper(self, tmp_path):
        """Create a BSArch wrapper for testing."""
        bsarch_path = tmp_path / "BSArch.exe"
        bsarch_path.write_text("fake bsarch")
        return ArchiveWrapper(ArchiveTool.BSARCH, bsarch_path, BuildMode.CLEAN)

    def test_initialization(self, tmp_path):
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
    def test_create_archive2_default_compression(self, mock_runner_class, archive2_wrapper, tmp_path):
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
    def test_create_archive2_xbox_compression(self, mock_runner_class, archive2_wrapper_xbox, tmp_path):
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
    def test_create_archive2_no_compression(self, mock_runner_class, archive2_wrapper, tmp_path):
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
    def test_create_archive2_with_file_list(self, mock_runner_class, archive2_wrapper, tmp_path):
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
    def test_create_bsarch_archive(self, mock_runner_class, bsarch_wrapper, tmp_path):
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
    def test_extract_archive2(self, mock_runner_class, archive2_wrapper, tmp_path):
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
    def test_extract_bsarch(self, mock_runner_class, bsarch_wrapper, tmp_path):
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

    def test_extract_nonexistent_archive(self, archive2_wrapper, tmp_path):
        """Test extraction of non-existent archive."""
        archive_path = tmp_path / "nonexistent.ba2"
        output_dir = tmp_path / "output"

        result = archive2_wrapper.extract_archive(archive_path, output_dir)

        assert result is False

    @patch("PrevisLib.tools.archive.ProcessRunner")
    @patch("PrevisLib.tools.archive.shutil")
    def test_add_to_archive_success(self, mock_shutil, mock_runner_class, archive2_wrapper, tmp_path):
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
    def test_create_archive_process_failure(self, mock_runner_class, archive2_wrapper, tmp_path):
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

    def test_build_mode_inheritance(self, tmp_path):
        """Test that build mode is properly inherited and accessible."""
        archive_path = tmp_path / "Archive2.exe"
        archive_path.write_text("fake archive2")

        # Test each build mode
        for mode in [BuildMode.CLEAN, BuildMode.FILTERED, BuildMode.XBOX]:
            wrapper = ArchiveWrapper(ArchiveTool.ARCHIVE2, archive_path, mode)
            assert wrapper.build_mode == mode

    @patch("PrevisLib.tools.archive.ProcessRunner")
    def test_compression_mode_combinations(self, mock_runner_class, tmp_path):
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
