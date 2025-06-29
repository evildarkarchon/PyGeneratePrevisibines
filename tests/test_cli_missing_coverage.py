"""Tests to improve coverage for remaining uncovered lines in previs_builder."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from previs_builder import main, show_build_summary, show_tool_versions
from PrevisLib.config.settings import Settings
from PrevisLib.models.data_classes import ArchiveTool, BuildMode, ToolPaths


class TestShowFunctions:
    """Test the show_* display functions."""

    @patch("previs_builder.console")
    @patch("previs_builder.check_tool_version")
    def test_show_tool_versions_all_found(self, mock_check_version, mock_console):
        """Test showing tool versions when all tools are found."""
        mock_check_version.side_effect = [
            (True, "Version: 1.0.0"),  # xEdit
            (True, "Version: 1.6.659.0"),  # Fallout4
            (True, "Version: 1.0.0.0"),  # CreationKit
        ]
        
        settings = Settings(
            plugin_name="test.esp",
            build_mode=BuildMode.CLEAN,
            tool_paths=ToolPaths(
                xedit=Path("/fake/FO4Edit.exe"),
                fallout4=Path("/fake/Fallout4.exe"),
                creation_kit=Path("/fake/CreationKit.exe"),
                archive2=Path("/fake/Archive2.exe")
            )
        )
        
        show_tool_versions(settings)
        
        # Verify all tools were checked
        assert mock_check_version.call_count == 3
        # Verify version display
        assert any("Using FO4Edit.exe V1.0.0" in str(call) for call in mock_console.print.call_args_list)
        assert any("Using Fallout4.exe V1.6.659.0" in str(call) for call in mock_console.print.call_args_list)
        assert any("Using CreationKit.exe V1.0.0.0" in str(call) for call in mock_console.print.call_args_list)

    @patch("previs_builder.console")
    @patch("previs_builder.check_tool_version")
    def test_show_tool_versions_not_found(self, mock_check_version, mock_console):
        """Test showing tool versions when tools are not found."""
        settings = Settings(
            plugin_name="test.esp",
            build_mode=BuildMode.CLEAN,
            tool_paths=ToolPaths(
                xedit=None,
                fallout4=None,
                creation_kit=None,
                archive2=Path("/fake/Archive2.exe")
            )
        )
        
        show_tool_versions(settings)
        
        # Verify "Not Found" messages
        assert any("Not Found" in str(call) for call in mock_console.print.call_args_list)

    @patch("previs_builder.console")
    def test_show_build_summary_with_ckpe(self, mock_console):
        """Test showing build summary with CKPE config."""
        settings = Settings(
            plugin_name="test.esp",
            build_mode=BuildMode.FILTERED,
            archive_tool=ArchiveTool.BSARCH,
            ckpe_config=Path("custom.json"),
            tool_paths=ToolPaths()
        )
        
        show_build_summary(settings)
        
        # Verify CKPE config is shown
        assert any("CKPE Config" in str(call) for call in mock_console.print.call_args_list)
        assert any("Loaded ✓" in str(call) for call in mock_console.print.call_args_list)


class TestEdgeCasesInMain:
    """Test remaining edge cases in main function."""

    @patch("previs_builder.setup_logger")
    @patch("previs_builder.Settings.from_cli_args")
    @patch("previs_builder.PrevisBuilder")
    @patch("previs_builder.prompt_for_plugin")
    @patch("previs_builder.Confirm.ask")
    def test_interactive_mode_cleanup_only(
        self,
        mock_confirm,
        mock_prompt_plugin,
        mock_previs_builder,
        mock_settings_from_cli,
        mock_setup_logger
    ):
        """Test interactive mode when user chooses cleanup only."""
        # Setup
        mock_settings = MagicMock()
        mock_settings.plugin_name = ""  # No plugin to trigger interactive
        mock_settings.tool_paths.validate.return_value = []
        mock_settings_from_cli.return_value = mock_settings
        
        mock_builder = MagicMock()
        mock_builder.cleanup.return_value = True
        mock_previs_builder.return_value = mock_builder
        
        mock_prompt_plugin.return_value = "Test.esp"
        mock_confirm.side_effect = [True, False]  # Yes to cleanup, No to build
        
        runner = CliRunner()
        result = runner.invoke(main, [])
        
        assert result.exit_code == 0
        mock_builder.cleanup.assert_called_once()

    @patch("previs_builder.setup_logger")
    @patch("previs_builder.Settings.from_cli_args")
    @patch("previs_builder.run_build")
    def test_run_argument_direct_to_build(
        self,
        mock_run_build,
        mock_settings_from_cli,
        mock_setup_logger
    ):
        """Test --run argument bypasses confirmation."""
        mock_settings = MagicMock()
        mock_settings.plugin_name = "test.esp"
        mock_settings.tool_paths.validate.return_value = []
        mock_settings_from_cli.return_value = mock_settings
        mock_run_build.return_value = True
        
        runner = CliRunner()
        result = runner.invoke(main, ["--run", "test.esp"])
        
        assert result.exit_code == 0
        mock_run_build.assert_called_once()


class TestLegacyModeHandling:
    """Test legacy mode argument combinations."""

    @patch("previs_builder.setup_logger")
    @patch("previs_builder.run_build")
    @patch("PrevisLib.config.settings.find_tool_paths")
    def test_legacy_mode_combinations(self, mock_find_tools, mock_run_build, mock_setup_logger):
        """Test various legacy mode combinations."""
        mock_tool_paths = MagicMock()
        mock_tool_paths.validate.return_value = []
        mock_find_tools.return_value = mock_tool_paths
        mock_run_build.return_value = True
        
        runner = CliRunner()
        
        # Test -clean with plugin position
        result = runner.invoke(main, ["-clean", "test.esp"])
        assert result.exit_code == 0
        
        # Test plugin first, then mode
        result = runner.invoke(main, ["test.esp", "-filtered"])
        assert result.exit_code == 0
        
        called_settings = mock_run_build.call_args[0][0]
        assert called_settings.build_mode == BuildMode.FILTERED