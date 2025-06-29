"""Tests to improve coverage for remaining uncovered lines in previs_builder."""

from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

from click.testing import CliRunner

from previs_builder import main, show_build_summary, show_tool_versions
from PrevisLib.config.settings import Settings
from PrevisLib.models.data_classes import ArchiveTool, BuildMode, CKPEConfig, ToolPaths


class TestShowFunctions:
    """Test the show_* display functions."""

    @patch("previs_builder.check_tool_version")
    @patch("pathlib.Path.exists", return_value=True)
    def test_show_tool_versions_all_found(self, mock_exists: MagicMock, mock_check_version: MagicMock) -> None:  # noqa: ARG002
        """Test showing tool versions when all tools are found."""
        mock_check_version.return_value = (True, "Version: 1.0.0")
        settings = Settings(
            plugin_name="test.esp",
            build_mode=BuildMode.CLEAN,
            tool_paths=ToolPaths(
                xedit=Path("/fake/FO4Edit.exe"),
                fallout4=Path("/fake/Fallout4.exe"),
                creation_kit=Path("/fake/CreationKit.exe"),
                archive2=Path("/fake/Archive2.exe"),
            ),
        )

        with patch("previs_builder.console"):
            show_tool_versions(settings)

        assert mock_check_version.call_count == 4

    @patch("previs_builder.console")
    @patch("previs_builder.check_tool_version")
    def test_show_tool_versions_not_found(self, mock_check_version: MagicMock, mock_console: MagicMock) -> None:
        """Test showing tool versions when tools are not found."""
        mock_check_version.return_value = (False, "")
        settings = Settings(
            plugin_name="test.esp",
            build_mode=BuildMode.CLEAN,
            tool_paths=ToolPaths(xedit=None, fallout4=None, creation_kit=None, archive2=Path("/fake/Archive2.exe")),
        )

        with patch("pathlib.Path.exists", return_value=False):
            show_tool_versions(settings)

        # Verify "Not Found" messages
        assert any("Not Found" in str(call) for call in mock_console.print.call_args_list)

    @patch("previs_builder.console")
    @patch("previs_builder.Table")
    def test_show_build_summary_with_ckpe(self, mock_table_class: MagicMock, mock_console: MagicMock) -> None:  # noqa: ARG002
        """Test showing build summary with CKPE config."""
        # Create settings first
        settings = Settings(
            plugin_name="test.esp",
            build_mode=BuildMode.FILTERED,
            archive_tool=ArchiveTool.BSARCH,
            tool_paths=ToolPaths(),
        )

        # Create a dummy CKPEConfig object using factory method with mocking
        with (
            patch("pathlib.Path.open", mock_open()),
            patch("configparser.ConfigParser.read"),
            patch("configparser.ConfigParser.has_section", return_value=True),
            patch("configparser.ConfigParser.sections", return_value=["CreationKit"]),
            patch("configparser.ConfigParser.items", return_value=[]),
            patch("configparser.ConfigParser.__getitem__", return_value={}),
        ):
            ckpe_config = CKPEConfig.from_ini(Path("dummy.ini"))

        # Set the ckpe_config on settings
        settings.ckpe_config = ckpe_config

        # Mock the Table instance
        mock_table = MagicMock()
        mock_table_class.return_value = mock_table

        show_build_summary(settings)

        # Verify CKPE config row was added to table
        add_row_calls = mock_table.add_row.call_args_list
        assert any("CKPE Config" in str(call) for call in add_row_calls)


class TestEdgeCasesInMain:
    """Test remaining edge cases in main function."""

    @patch("previs_builder.setup_logger")
    @patch("previs_builder.Settings.from_cli_args")
    @patch("previs_builder.PrevisBuilder")
    @patch("previs_builder.prompt_for_plugin")
    @patch("previs_builder.Confirm.ask")
    def test_interactive_mode_cleanup_only(
        self,
        mock_confirm: MagicMock,
        mock_prompt_plugin: MagicMock,
        mock_previs_builder: MagicMock,
        mock_settings_from_cli: MagicMock,
        mock_setup_logger: MagicMock,  # noqa: ARG002
    ) -> None:
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
        mock_confirm.side_effect = [True, True]  # Yes to cleanup, Yes to proceed

        runner = CliRunner()
        result = runner.invoke(main, [])

        assert result.exit_code == 0
        mock_builder.cleanup.assert_called_once()

    @patch("previs_builder.setup_logger")
    @patch("previs_builder.Settings.from_cli_args")
    @patch("previs_builder.run_build")
    def test_run_argument_direct_to_build(
        self, mock_run_build: MagicMock, mock_settings_from_cli: MagicMock, mock_setup_logger: MagicMock  # noqa: ARG002
    ) -> None:
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
    def test_legacy_mode_combinations(self, mock_find_tools: MagicMock, mock_run_build: MagicMock, mock_setup_logger: MagicMock) -> None:  # noqa: ARG002
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
