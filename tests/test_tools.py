"""Tests for tool wrapper classes."""

from unittest.mock import Mock, patch

import pytest

from PrevisLib.models.data_classes import BuildMode, CKPEConfig
from PrevisLib.tools.creation_kit import CreationKitWrapper


class TestCreationKit:
    """Test Creation Kit wrapper."""

    @pytest.fixture
    def wrapper(self, tmp_path):
        """Create a CreationKit wrapper for testing."""
        ck_path = tmp_path / "CreationKit.exe"
        ck_path.write_text("fake ck")
        return CreationKitWrapper(ck_path, "TestMod.esp", BuildMode.CLEAN, None)

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
        mock_runner.run_process.return_value = True
        mock_runner_class.return_value = mock_runner
        wrapper.process_runner = mock_runner

        data_path = tmp_path / "Data"

        with patch.object(wrapper, "_check_ck_errors", return_value=False):
            result = wrapper.generate_precombined(data_path)

        assert result is True
        mock_runner.run_process.assert_called_once()

        # Check command arguments
        args = mock_runner.run_process.call_args[0][0]
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
        mock_runner.run_process.return_value = True
        mock_runner_class.return_value = mock_runner
        wrapper.process_runner = mock_runner

        data_path = tmp_path / "Data"

        with patch.object(wrapper, "_check_ck_errors", return_value=False):
            result = wrapper.generate_precombined(data_path)

        assert result is True
        args = mock_runner.run_process.call_args[0][0]
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
        mock_runner.run_process.return_value = True
        mock_runner_class.return_value = mock_runner
        wrapper.process_runner = mock_runner

        data_path = tmp_path / "Data"

        with patch.object(wrapper, "_check_ck_errors", return_value=False):
            result = wrapper.generate_precombined(data_path)

        assert result is True
        args = mock_runner.run_process.call_args[0][0]
        # Xbox mode still uses "filtered" and "all" (non-clean mode)
        assert "filtered" in args
        assert "all" in args

    @patch("PrevisLib.tools.creation_kit.ProcessRunner")
    def test_generate_precombined_process_failure(self, mock_runner_class, wrapper, tmp_path):
        """Test precombined generation when process fails."""
        mock_runner = Mock()
        mock_runner.run_process.return_value = False
        mock_runner_class.return_value = mock_runner
        wrapper.process_runner = mock_runner

        data_path = tmp_path / "Data"

        result = wrapper.generate_precombined(data_path)

        assert result is False

    @patch("PrevisLib.tools.creation_kit.ProcessRunner")
    def test_generate_precombined_ck_errors(self, mock_runner_class, wrapper, tmp_path):
        """Test precombined generation when CK reports errors."""
        mock_runner = Mock()
        mock_runner.run_process.return_value = True
        mock_runner_class.return_value = mock_runner
        wrapper.process_runner = mock_runner

        data_path = tmp_path / "Data"

        with patch.object(wrapper, "_check_ck_errors", return_value=True):
            result = wrapper.generate_precombined(data_path)

        assert result is False

    @patch("PrevisLib.tools.creation_kit.ProcessRunner")
    def test_compress_psg_success(self, mock_runner_class, wrapper, tmp_path):
        """Test successful PSG compression."""
        mock_runner = Mock()
        mock_runner.run_process.return_value = True
        mock_runner_class.return_value = mock_runner
        wrapper.process_runner = mock_runner

        data_path = tmp_path / "Data"

        with patch.object(wrapper, "_check_ck_errors", return_value=False):
            result = wrapper.compress_psg(data_path)

        assert result is True
        mock_runner.run_process.assert_called_once()

        # Check timeout and command
        call_args = mock_runner.run_process.call_args
        assert call_args[1]["timeout"] == 600

    @patch("PrevisLib.tools.creation_kit.ProcessRunner")
    def test_build_cdx_success(self, mock_runner_class, wrapper, tmp_path):
        """Test successful CDX building."""
        mock_runner = Mock()
        mock_runner.run_process.return_value = True
        mock_runner_class.return_value = mock_runner
        wrapper.process_runner = mock_runner

        data_path = tmp_path / "Data"

        with patch.object(wrapper, "_check_ck_errors", return_value=False):
            result = wrapper.build_cdx(data_path)

        assert result is True
        mock_runner.run_process.assert_called_once()

        # Check timeout
        call_args = mock_runner.run_process.call_args
        assert call_args[1]["timeout"] == 900

    @patch("PrevisLib.tools.creation_kit.ProcessRunner")
    def test_generate_previs_data_success(self, mock_runner_class, wrapper, tmp_path):
        """Test successful previs data generation."""
        mock_runner = Mock()
        mock_runner.run_process.return_value = True
        mock_runner_class.return_value = mock_runner
        wrapper.process_runner = mock_runner

        data_path = tmp_path / "Data"

        with patch.object(wrapper, "_check_ck_errors", return_value=False):
            with patch.object(wrapper, "_check_previs_completion", return_value=True):
                result = wrapper.generate_previs_data(data_path)

        assert result is True
        mock_runner.run_process.assert_called_once()

        # Check timeout (should be 172800 - 2 days)
        call_args = mock_runner.run_process.call_args
        assert call_args[1]["timeout"] == 172800
        
        # Check command arguments
        args = mock_runner.run_process.call_args[0][0]
        assert str(wrapper.ck_path) in args
        assert f"-GeneratePreVisData:{wrapper.plugin_name}" in args
        assert "clean" in args
        assert "all" in args

    @patch("PrevisLib.tools.creation_kit.ProcessRunner")
    def test_generate_previs_data_completion_failure(self, mock_runner_class, wrapper, tmp_path):
        """Test previs data generation when completion check fails."""
        mock_runner = Mock()
        mock_runner.run_process.return_value = True
        mock_runner_class.return_value = mock_runner
        wrapper.process_runner = mock_runner

        data_path = tmp_path / "Data"

        with patch.object(wrapper, "_check_ck_errors", return_value=False):
            with patch.object(wrapper, "_check_previs_completion", return_value=False):
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

        # Test each error pattern
        error_patterns = ["OUT OF HANDLE ARRAY ENTRIES", "Failed to load", "ERROR:", "FATAL:", "Exception"]

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

        failure_patterns = ["visibility task did not complete", "Previs generation failed", "Could not complete previs"]

        for pattern in failure_patterns:
            log_file.write_text(f"Some content\n{pattern}\nMore content")

            result = wrapper._check_previs_completion(data_path)
            assert result is False

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

        # Test with error in custom log
        log_path.write_text("Some content\nOUT OF HANDLE ARRAY ENTRIES\nMore content")
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
