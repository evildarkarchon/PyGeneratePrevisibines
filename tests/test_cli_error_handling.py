"""Tests for error handling and edge cases in previs_builder."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from previs_builder import main, run_build
from PrevisLib.models.data_classes import BuildMode, ArchiveTool


class TestRunBuildErrorHandling:
    """Test error handling in run_build function."""

    @patch("previs_builder.PrevisBuilder")
    @patch("previs_builder.console")
    def test_run_build_general_exception(self, mock_console, mock_previs_builder):
        """Test run_build handling of general exceptions."""
        mock_settings = MagicMock()
        mock_settings.plugin_name = "test.esp"
        mock_settings.build_mode = BuildMode.CLEAN
        mock_settings.archive_tool = ArchiveTool.ARCHIVE2
        mock_builder = MagicMock()
        mock_builder.failed_step = None
        mock_builder.build.side_effect = Exception("Unexpected error")
        mock_previs_builder.return_value = mock_builder

        with pytest.raises(Exception, match="Unexpected error"), patch("previs_builder.Confirm.ask", return_value=True):
            run_build(mock_settings)

    @patch("previs_builder.PrevisBuilder")
    @patch("previs_builder.console")
    def test_run_build_builder_init_exception(self, mock_console, mock_previs_builder):
        """Test run_build when PrevisBuilder initialization fails."""
        mock_settings = MagicMock()
        mock_previs_builder.side_effect = ValueError("Invalid configuration")

        with pytest.raises(ValueError, match="Invalid configuration"):
            run_build(mock_settings)

    @patch("previs_builder.PrevisBuilder")
    @patch("previs_builder.Confirm.ask")
    def test_run_build_cleanup_working_files_error(self, mock_confirm, mock_previs_builder):
        """Test handling of cleanup_working_files errors."""
        mock_settings = MagicMock()
        mock_settings.plugin_name = "test.esp"
        mock_settings.build_mode = BuildMode.CLEAN
        mock_settings.archive_tool = ArchiveTool.ARCHIVE2
        mock_builder = MagicMock()
        mock_builder.failed_step = None
        mock_builder.build.return_value = True
        mock_builder.cleanup_working_files.side_effect = Exception("Cleanup failed")
        mock_previs_builder.return_value = mock_builder
        mock_confirm.return_value = True  # Yes to build, Yes to cleanup

        # Should not raise exception, just return success from build
        result = run_build(mock_settings)

        assert result is True  # Build succeeded even if cleanup failed


class TestMainCLIEdgeCases:
    """Test edge cases in main CLI function."""

    @patch("previs_builder.setup_logger")
    @patch("previs_builder.Settings.from_cli_args")
    def test_main_unexpected_exception(self, mock_settings_from_cli, mock_setup_logger):
        """Test handling of unexpected exceptions in main."""
        mock_settings_from_cli.side_effect = RuntimeError("Unexpected error")

        runner = CliRunner()
        result = runner.invoke(main, ["MyMod.esp"])

        assert result.exit_code == 1
        assert "Unexpected error:" in result.output
        assert "Unexpected error" in result.output

    @patch("previs_builder.setup_logger")
    @patch("previs_builder.Settings.from_cli_args")
    @patch("previs_builder.run_build")
    def test_main_build_failure(self, mock_run_build, mock_settings_from_cli, mock_setup_logger):
        """Test main when build fails."""
        mock_settings = MagicMock()
        mock_settings.tool_paths.validate.return_value = []
        mock_settings_from_cli.return_value = mock_settings
        mock_run_build.return_value = False

        runner = CliRunner()
        result = runner.invoke(main, ["MyMod.esp"])

        assert result.exit_code == 1
        assert "Build completed successfully!" not in result.output

    @patch("previs_builder.setup_logger")
    @patch("previs_builder.Settings.from_cli_args")
    @patch("previs_builder.PrevisBuilder")
    @patch("previs_builder.Confirm.ask")
    def test_main_cleanup_error(self, mock_confirm, mock_previs_builder, mock_settings_from_cli, mock_setup_logger):
        """Test handling of cleanup errors."""
        mock_settings = MagicMock()
        mock_settings.plugin_name = ""
        mock_settings.tool_paths.validate.return_value = []
        mock_settings_from_cli.return_value = mock_settings

        mock_builder = MagicMock()
        mock_builder.cleanup.side_effect = Exception("Cleanup failed")
        mock_previs_builder.return_value = mock_builder

        mock_confirm.return_value = True  # Yes to cleanup

        runner = CliRunner()
        with patch("previs_builder.prompt_for_plugin", return_value="Test.esp"):
            result = runner.invoke(main, [])

        assert result.exit_code == 0  # Cleanup errors don't fail the program
        mock_builder.cleanup.assert_called_once()


class TestLegacyArgumentHandling:
    """Test handling of legacy command line arguments."""

    @patch("previs_builder.setup_logger")
    @patch("previs_builder.run_build")
    @patch("PrevisLib.config.settings.find_tool_paths")
    def test_legacy_xbox_mode(self, mock_tool_discover, mock_run_build, mock_setup_logger):
        """Test parsing of legacy -xbox argument."""
        mock_tool_paths = MagicMock()
        mock_tool_paths.validate.return_value = []
        mock_tool_discover.return_value = mock_tool_paths
        mock_run_build.return_value = True

        runner = CliRunner()
        result = runner.invoke(main, ["-xbox", "MyMod.esp"])

        assert result.exit_code == 0
        called_settings = mock_run_build.call_args[0][0]
        assert called_settings.build_mode == BuildMode.XBOX

    @patch("previs_builder.setup_logger")
    @patch("previs_builder.run_build")
    @patch("PrevisLib.config.settings.find_tool_paths")
    def test_multiple_legacy_modes(self, mock_tool_discover, mock_run_build, mock_setup_logger):
        """Test handling of conflicting legacy mode arguments."""
        mock_tool_paths = MagicMock()
        mock_tool_paths.validate.return_value = []
        mock_tool_discover.return_value = mock_tool_paths
        mock_run_build.return_value = True

        runner = CliRunner()
        # When multiple modes are specified, last one wins
        result = runner.invoke(main, ["-clean", "-filtered", "-xbox", "MyMod.esp"])

        assert result.exit_code == 0
        called_settings = mock_run_build.call_args[0][0]
        assert called_settings.build_mode == BuildMode.XBOX


class TestToolPathValidation:
    """Test tool path validation edge cases."""

    @patch("previs_builder.setup_logger")
    @patch("previs_builder.Settings.from_cli_args")
    @patch("previs_builder.console")
    def test_multiple_tool_validation_errors(self, mock_console, mock_settings_from_cli, mock_setup_logger):
        """Test handling of multiple tool validation errors."""
        mock_settings = MagicMock()
        mock_settings.tool_paths.validate.return_value = ["Creation Kit not found", "xEdit not found", "Archive2 not found"]
        mock_settings_from_cli.return_value = mock_settings

        runner = CliRunner()
        result = runner.invoke(main, ["MyMod.esp"])

        assert result.exit_code == 1
        # All errors should be printed
        output_calls = [str(call) for call in mock_console.print.call_args_list]
        assert any("Creation Kit not found" in call for call in output_calls)
        assert any("xEdit not found" in call for call in output_calls)
        assert any("Archive2 not found" in call for call in output_calls)
