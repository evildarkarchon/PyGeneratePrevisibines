"""Consolidated tests for command line interface functionality."""

from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest
from click.testing import CliRunner

from previs_builder import main, prompt_for_plugin, run_build, show_build_summary, show_tool_versions
from PrevisLib.config.settings import Settings
from PrevisLib.models.data_classes import ArchiveTool, BuildMode, BuildStep, CKPEConfig, ToolPaths


class TestCLIPathOverrides:
    """Test CLI path override functionality."""

    @patch("PrevisLib.config.settings.find_tool_paths")
    def test_fallout4_path_override(self, mock_find_tools: MagicMock) -> None:
        """Test that --fallout4-path correctly overrides tool discovery."""
        # Mock the default tool discovery
        mock_tool_paths = ToolPaths()
        mock_find_tools.return_value = mock_tool_paths

        # Create a fake Fallout 4 installation directory
        fake_fo4_path = Path("/fake/fallout4")
        fake_fo4_exe = fake_fo4_path / "Fallout4.exe"
        fake_ck_exe = fake_fo4_path / "CreationKit.exe"
        fake_archive_exe = fake_fo4_path / "Tools" / "Archive2" / "Archive2.exe"

        # Mock file existence by patching the exists method to return True for our test paths
        def mock_exists(self) -> bool:  # noqa: ANN001
            return self in [fake_fo4_exe, fake_ck_exe, fake_archive_exe]

        with patch.object(Path, "exists", mock_exists):
            # Test the override
            settings = Settings.from_cli_args(fallout4_path=fake_fo4_path)

            assert settings.tool_paths.fallout4 == fake_fo4_exe
            assert settings.tool_paths.creation_kit == fake_ck_exe
            assert settings.tool_paths.archive2 == fake_archive_exe

    @patch("PrevisLib.config.settings.find_tool_paths")
    def test_xedit_path_override(self, mock_find_tools: MagicMock) -> None:
        """Test that --xedit-path correctly overrides tool discovery."""
        # Mock the default tool discovery
        mock_tool_paths = ToolPaths()
        mock_find_tools.return_value = mock_tool_paths

        # Create a fake xEdit path
        fake_xedit_path = Path("/fake/tools/FO4Edit.exe")
        fake_bsarch_path = fake_xedit_path.parent / "BSArch.exe"

        # Mock file existence by patching the exists method to return True for our test paths
        def mock_exists(self) -> bool:  # noqa: ANN001
            return self in [fake_xedit_path, fake_bsarch_path]

        with patch.object(Path, "exists", mock_exists):
            # Test the override
            settings = Settings.from_cli_args(xedit_path=fake_xedit_path)

            assert settings.tool_paths.xedit == fake_xedit_path
            assert settings.tool_paths.bsarch == fake_bsarch_path

    @patch("PrevisLib.config.settings.find_tool_paths")
    def test_fallout4_path_missing_exe_raises_error(self, mock_find_tools: MagicMock) -> None:
        """Test that missing Fallout4.exe in specified path raises error."""
        mock_tool_paths = ToolPaths()
        mock_find_tools.return_value = mock_tool_paths

        fake_fo4_path = Path("/fake/fallout4")

        with patch.object(Path, "exists", return_value=False), pytest.raises(ValueError, match="Fallout4.exe not found in specified path"):
            Settings.from_cli_args(fallout4_path=fake_fo4_path)


class TestPluginPrompting:
    """Test plugin name prompting functionality."""

    @patch("previs_builder.Prompt.ask")
    @patch("previs_builder.Confirm.ask")
    def test_prompt_for_plugin_exit(self, mock_confirm: MagicMock, mock_prompt: MagicMock) -> None:
        """Test exiting plugin prompt with KeyboardInterrupt."""
        mock_prompt.side_effect = KeyboardInterrupt()
        mock_confirm.return_value = True

        with pytest.raises(KeyboardInterrupt):
            prompt_for_plugin()

    @patch("previs_builder.Prompt.ask")
    @patch("previs_builder.console.print")
    def test_prompt_for_plugin_validation_error(self, mock_print: MagicMock, mock_prompt: MagicMock) -> None:
        """Test plugin validation error handling."""
        # First call returns invalid name, second call raises KeyboardInterrupt to exit
        mock_prompt.side_effect = ["invalid name with spaces", KeyboardInterrupt()]

        with patch("previs_builder.Confirm.ask", return_value=True), pytest.raises(KeyboardInterrupt):
            prompt_for_plugin()

        # Should have printed an error about spaces
        mock_print.assert_any_call("\n[red]Error:[/red] Plugin name cannot contain spaces")

    @patch("previs_builder.validate_plugin_name")
    @patch("previs_builder.Prompt.ask")
    def test_prompt_for_plugin_valid_name(self, mock_prompt: MagicMock, mock_validate: MagicMock) -> None:
        """Test successful plugin name validation."""
        mock_prompt.return_value = "TestMod.esp"
        mock_validate.return_value = (True, "")

        result = prompt_for_plugin()
        assert result == "TestMod.esp"


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


class TestMainCLI:
    """Test the main CLI entry point."""

    @patch("previs_builder.setup_logger")
    @patch("previs_builder.Settings.from_cli_args")
    @patch("previs_builder.PrevisBuilder")
    def test_successful_build_non_interactive(
        self,
        mock_previs_builder: MagicMock,
        mock_settings_from_cli: MagicMock,
        mock_setup_logger: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test a successful build in non-interactive mode."""
        mock_settings = MagicMock()
        mock_settings.plugin_name = "MyMod.esp"
        mock_settings.build_mode = BuildMode.CLEAN
        mock_settings.archive_tool = ArchiveTool.ARCHIVE2
        mock_settings.ckpe_config = None
        mock_settings.tool_paths.validate.return_value = []
        mock_settings_from_cli.return_value = mock_settings

        mock_builder = MagicMock()
        mock_builder.build.return_value = True
        mock_builder.failed_step = None  # No previous failed build
        mock_previs_builder.return_value = mock_builder

        runner = CliRunner()
        # Mocking Confirm.ask to automatically say "yes" to "Proceed with build?"
        with patch("previs_builder.Confirm.ask", return_value=True):
            result = runner.invoke(main, ["MyMod.esp"])

        assert result.exit_code == 0
        assert "Build completed successfully!" in result.output
        mock_previs_builder.assert_called_with(mock_settings)
        mock_builder.build.assert_called_once()

    @patch("previs_builder.setup_logger")
    @patch("previs_builder.sys.platform", "win32")
    @patch("PrevisLib.utils.validation.validate_xedit_scripts")
    @patch("PrevisLib.config.settings.find_tool_paths")
    def test_tool_validation_failure(
        self,
        mock_find_tools: MagicMock,
        mock_validate_scripts: MagicMock,
        mock_setup_logger: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test that the application exits if tool validation fails."""
        # Mock tool discovery to return empty ToolPaths
        from PrevisLib.models.data_classes import ToolPaths
        mock_tool_paths = ToolPaths()
        mock_find_tools.return_value = mock_tool_paths
        
        # Mock script validation to pass
        mock_validate_scripts.return_value = (True, "")

        runner = CliRunner()
        result = runner.invoke(main, ["MyMod.esp"])

        assert result.exit_code == 1
        assert "Tool Configuration Issues" in result.output
        assert "Creation Kit not found" in result.output
        assert "Cannot proceed without required tools" in result.output

    def test_non_windows_warning(self) -> None:
        """Test that a warning is shown on non-Windows platforms."""
        with (
            patch("previs_builder.setup_logger"),
            patch("previs_builder.sys.platform", "linux"),
            patch("previs_builder.platform.system", return_value="Linux"),
            patch("previs_builder.Settings.from_cli_args") as mock_settings_from_cli,
            patch("previs_builder.run_build", return_value=True) as mock_run_build,
        ):
            mock_settings = MagicMock()
            mock_settings.plugin_name = "MyMod.esp"
            mock_settings.build_mode = BuildMode.CLEAN
            mock_settings.archive_tool = ArchiveTool.ARCHIVE2
            mock_settings.ckpe_config = None
            mock_settings.tool_paths.validate.return_value = []
            mock_settings_from_cli.return_value = mock_settings

            runner = CliRunner()
            result = runner.invoke(main, ["MyMod.esp"])

            assert result.exit_code == 0
            assert "Running on non-Windows platform" in result.output
            mock_run_build.assert_called_once()

    @patch("previs_builder.setup_logger")
    def test_help_message(self, mock_setup_logger: MagicMock) -> None:  # noqa: ARG002
        """Test that the --help message is displayed correctly."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Usage: main [OPTIONS] [ARGS]..." in result.output
        assert "Automated previs generation for Fallout 4" in result.output

    @patch("previs_builder.setup_logger")
    @patch("previs_builder.Settings.from_cli_args")
    @patch("previs_builder.PrevisBuilder")
    def test_keyboard_interrupt_handling(
        self,
        mock_previs_builder: MagicMock,  # noqa: ARG002
        mock_settings_from_cli: MagicMock,
        mock_setup_logger: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test that KeyboardInterrupt is handled gracefully."""
        mock_settings_from_cli.side_effect = KeyboardInterrupt
        runner = CliRunner()
        result = runner.invoke(main, [])

        assert result.exit_code == 130
        assert "Build cancelled by user" in result.output

    @patch("previs_builder.setup_logger")
    @patch("previs_builder.Settings.from_cli_args")
    @patch("previs_builder.PrevisBuilder")
    @patch("previs_builder.prompt_for_plugin")
    @patch("previs_builder.prompt_for_build_mode")
    @patch("previs_builder.Confirm.ask")
    def test_successful_build_interactive(  # noqa: PLR0913
        self,
        mock_confirm: MagicMock,
        mock_prompt_build_mode: MagicMock,
        mock_prompt_plugin: MagicMock,
        mock_previs_builder: MagicMock,
        mock_settings_from_cli: MagicMock,
        mock_setup_logger: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test a successful build in fully interactive mode."""
        # Simulate interactive session:
        # 1. Not cleaning up -> False
        # 2. Provide plugin name
        # 3. Select build mode
        # 4. Confirm to proceed with build -> True
        mock_settings = MagicMock()
        mock_settings.plugin_name = ""  # Start with no plugin
        mock_settings.build_mode = BuildMode.CLEAN
        mock_settings.archive_tool = ArchiveTool.ARCHIVE2
        mock_settings.ckpe_config = None
        mock_settings.tool_paths.validate.return_value = []
        mock_settings_from_cli.return_value = mock_settings

        mock_builder = MagicMock()
        mock_builder.build.return_value = True
        mock_builder.failed_step = None  # No previous failed build
        mock_previs_builder.return_value = mock_builder

        mock_prompt_plugin.return_value = "MyInteractiveMod.esp"
        mock_prompt_build_mode.return_value = BuildMode.FILTERED
        mock_confirm.side_effect = [False, True, True]  # No to cleanup, Yes to build, Yes to cleanup working files

        runner = CliRunner()
        result = runner.invoke(main, [])

        assert result.exit_code == 0
        assert "Build completed successfully!" in result.output
        mock_prompt_plugin.assert_called_once()
        mock_prompt_build_mode.assert_called_once()
        # settings object is updated in place
        assert mock_settings.plugin_name == "MyInteractiveMod.esp"
        assert mock_settings.build_mode == BuildMode.FILTERED
        mock_builder.build.assert_called_once()

    @patch("previs_builder.setup_logger")
    @patch("previs_builder.Settings.from_cli_args")
    @patch("previs_builder.PrevisBuilder")
    @patch("previs_builder.prompt_for_resume")
    def test_resume_build_flow(  # noqa: PLR0913
        self,
        mock_prompt_resume: MagicMock,
        mock_previs_builder: MagicMock,
        mock_settings_from_cli: MagicMock,
        mock_setup_logger: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test the build resume flow."""
        mock_settings = MagicMock()
        mock_settings.plugin_name = "MyMod.esp"
        mock_settings.build_mode = BuildMode.CLEAN
        mock_settings.archive_tool = ArchiveTool.ARCHIVE2
        mock_settings.ckpe_config = None
        mock_settings.tool_paths.validate.return_value = []
        mock_settings_from_cli.return_value = mock_settings

        mock_builder = MagicMock()
        mock_builder.failed_step = BuildStep.GENERATE_PRECOMBINED
        mock_builder.build.return_value = True
        mock_previs_builder.return_value = mock_builder

        mock_prompt_resume.return_value = BuildStep.GENERATE_PRECOMBINED

        runner = CliRunner()
        with patch("previs_builder.Confirm.ask", return_value=True):
            result = runner.invoke(main, ["MyMod.esp"])

        assert result.exit_code == 0
        mock_prompt_resume.assert_called_once()
        mock_builder.build.assert_called_with(start_from_step=BuildStep.GENERATE_PRECOMBINED)

    @patch("previs_builder.setup_logger")
    @patch("previs_builder.run_build")
    @patch("PrevisLib.config.settings.find_tool_paths")
    def test_run_argument_direct_to_build(
        self,
        mock_find_tools: MagicMock,
        mock_run_build: MagicMock,
        mock_setup_logger: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test --run argument bypasses confirmation."""
        mock_tool_paths = MagicMock()
        mock_tool_paths.validate.return_value = []
        mock_find_tools.return_value = mock_tool_paths
        mock_run_build.return_value = True

        runner = CliRunner()
        result = runner.invoke(main, ["--run", "test.esp"])

        assert result.exit_code == 0
        mock_run_build.assert_called_once()


class TestRunBuildErrorHandling:
    """Test error handling in run_build function."""

    @patch("previs_builder.PrevisBuilder")
    @patch("previs_builder.console")
    def test_run_build_general_exception(self, mock_console: MagicMock, mock_previs_builder: MagicMock) -> None:  # noqa: ARG002
        """Test run_build handling of general exceptions."""
        mock_settings = MagicMock()
        mock_settings.plugin_name = "test.esp"
        mock_settings.build_mode = BuildMode.CLEAN
        mock_settings.archive_tool = ArchiveTool.ARCHIVE2
        mock_settings.ckpe_config = None
        mock_builder = MagicMock()
        mock_builder.failed_step = None
        mock_builder.build.side_effect = Exception("Unexpected error")
        mock_previs_builder.return_value = mock_builder

        with pytest.raises(Exception, match="Unexpected error"), patch("previs_builder.Confirm.ask", return_value=True):
            run_build(mock_settings)

    @patch("previs_builder.PrevisBuilder")
    @patch("previs_builder.console")
    def test_run_build_builder_init_exception(self, mock_console: MagicMock, mock_previs_builder: MagicMock) -> None:  # noqa: ARG002
        """Test run_build when PrevisBuilder initialization fails."""
        mock_settings = MagicMock()
        mock_previs_builder.side_effect = ValueError("Invalid configuration")

        with pytest.raises(ValueError, match="Invalid configuration"):
            run_build(mock_settings)

    @patch("previs_builder.PrevisBuilder")
    @patch("previs_builder.Confirm.ask")
    def test_run_build_cleanup_working_files_error(self, mock_confirm: MagicMock, mock_previs_builder: MagicMock) -> None:
        """Test handling of cleanup_working_files errors."""
        mock_settings = MagicMock()
        mock_settings.plugin_name = "test.esp"
        mock_settings.build_mode = BuildMode.CLEAN
        mock_settings.archive_tool = ArchiveTool.ARCHIVE2
        mock_settings.ckpe_config = None
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
    def test_main_unexpected_exception(self, mock_settings_from_cli: MagicMock, mock_setup_logger: MagicMock) -> None:  # noqa: ARG002
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
    def test_main_build_failure(self, mock_run_build: MagicMock, mock_settings_from_cli: MagicMock, mock_setup_logger: MagicMock) -> None:  # noqa: ARG002
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
    @patch("previs_builder.prompt_for_plugin")
    @patch("previs_builder.Confirm.ask")
    @patch("previs_builder.console")
    def test_main_interactive_cleanup_success_then_exit(  # noqa: PLR0913
        self,
        mock_console: MagicMock,  # noqa: ARG002
        mock_confirm: MagicMock,
        mock_prompt_plugin: MagicMock,
        mock_builder_class: MagicMock,
        mock_settings_from_cli: MagicMock,
        mock_setup_logger: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test interactive mode: cleanup success, then exit without build."""
        # Setup
        mock_settings = MagicMock()
        mock_settings.plugin_name = ""
        mock_settings.build_mode = BuildMode.CLEAN
        mock_settings.archive_tool = ArchiveTool.ARCHIVE2
        mock_settings.ckpe_config = None
        mock_settings.tool_paths.validate.return_value = []
        mock_settings_from_cli.return_value = mock_settings

        mock_builder = MagicMock()
        mock_builder.cleanup.return_value = True
        mock_builder.failed_step = None  # No previous failed build
        mock_builder_class.return_value = mock_builder

        mock_prompt_plugin.return_value = "Cleaned.esp"
        mock_confirm.side_effect = [True, True]  # Yes to cleanup, then yes to proceed in cleanup prompt

        runner = CliRunner()
        result = runner.invoke(main, [])

        assert result.exit_code == 0
        mock_builder.cleanup.assert_called_once()


class TestLegacyArgumentHandling:
    """Test handling of legacy command line arguments."""

    @patch("previs_builder.setup_logger")
    @patch("previs_builder.run_build")
    @patch("PrevisLib.config.settings.find_tool_paths")
    def test_legacy_xbox_mode(self, mock_tool_discover: MagicMock, mock_run_build: MagicMock, mock_setup_logger: MagicMock) -> None:  # noqa: ARG002
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
    def test_multiple_legacy_modes(self, mock_tool_discover: MagicMock, mock_run_build: MagicMock, mock_setup_logger: MagicMock) -> None:  # noqa: ARG002
        """Test handling of multiple legacy mode arguments."""
        mock_tool_paths = MagicMock()
        mock_tool_paths.validate.return_value = []
        mock_tool_discover.return_value = mock_tool_paths
        mock_run_build.return_value = True

        runner = CliRunner()
        # Last mode should win
        result = runner.invoke(main, ["-clean", "-filtered", "-xbox", "MyMod.esp"])

        assert result.exit_code == 0
        called_settings = mock_run_build.call_args[0][0]
        assert called_settings.build_mode == BuildMode.XBOX


class TestCommandLineArguments:
    """Test various command line argument combinations."""

    @pytest.mark.parametrize(
        ("cli_args", "expected_plugin", "expected_mode", "expected_bsarch"),
        [
            # Case 1: Legacy, plugin only -> defaults to clean
            (["MyPlugin.esp"], "MyPlugin.esp", BuildMode.CLEAN, False),
            # Case 2: Legacy, explicit clean
            (["-clean", "MyPlugin.esp"], "MyPlugin.esp", BuildMode.CLEAN, False),
            # Case 3: Legacy, filtered
            (["-filtered", "MyPlugin.esp"], "MyPlugin.esp", BuildMode.FILTERED, False),
            # Case 4: Legacy, bsarch only -> Settings model defaults to clean
            (["-bsarch", "MyPlugin.esp"], "MyPlugin.esp", BuildMode.CLEAN, True),
            # Case 5: Modern, plugin only -> Settings model defaults to clean
            (["--plugin", "MyPlugin.esp"], "MyPlugin.esp", BuildMode.CLEAN, False),
            # Case 6: Modern, explicit xbox
            (
                ["--plugin", "MyPlugin.esp", "--build-mode", "xbox"],
                "MyPlugin.esp",
                BuildMode.XBOX,
                False,
            ),
            # Case 7: Mixed, modern build_mode overrides legacy
            (
                ["-filtered", "--build-mode", "clean", "MyPlugin.esp"],
                "MyPlugin.esp",
                BuildMode.CLEAN,
                False,
            ),
        ],
    )
    @patch("previs_builder.setup_logger")
    @patch("previs_builder.run_build")
    @patch("PrevisLib.config.settings.find_tool_paths")
    def test_argument_parsing(  # noqa: PLR0913
        self,
        mock_tool_discover: MagicMock,
        mock_run_build: MagicMock,
        mock_setup_logger: MagicMock,  # noqa: ARG002
        cli_args: list[str],
        expected_plugin: str,
        expected_mode: BuildMode,
        expected_bsarch: bool,
    ) -> None:
        """Test argument parsing for different combinations."""
        mock_tool_paths = MagicMock()
        mock_tool_paths.validate.return_value = []
        mock_tool_discover.return_value = mock_tool_paths
        mock_run_build.return_value = True

        runner = CliRunner()
        result = runner.invoke(main, cli_args)

        assert result.exit_code == 0
        called_settings = mock_run_build.call_args[0][0]
        assert called_settings.plugin_name == expected_plugin
        assert called_settings.build_mode == expected_mode
        if expected_bsarch:
            assert called_settings.archive_tool == ArchiveTool.BSARCH
        else:
            assert called_settings.archive_tool == ArchiveTool.ARCHIVE2
