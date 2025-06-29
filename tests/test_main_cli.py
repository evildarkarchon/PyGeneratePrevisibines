"""Main CLI tests for previs_builder."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from previs_builder import main
from PrevisLib.models.data_classes import ArchiveTool, BuildMode, BuildStep, ToolPaths


@pytest.fixture
def mock_settings() -> MagicMock:
    """Fixture to provide a mock Settings object."""
    settings = MagicMock()
    settings.plugin_name = "MyTestPlugin.esp"
    settings.build_mode = BuildMode.CLEAN
    settings.archive_tool.value = "Archive2"
    settings.ckpe_config = None
    settings.tool_paths.validate.return_value = []
    return settings


@pytest.fixture
def mock_builder() -> MagicMock:
    """Fixture to provide a mock PrevisBuilder."""
    builder = MagicMock()
    builder.failed_step = None
    builder.get_resume_options.return_value = [BuildStep.GENERATE_PRECOMBINED]
    builder.build.return_value = True
    builder.cleanup.return_value = True
    builder.cleanup_working_files.return_value = True
    return builder


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
        mock_settings: MagicMock,
        mock_builder: MagicMock,
    ) -> None:
        """Test a successful build in non-interactive mode."""
        mock_settings.plugin_name = "MyMod.esp"
        mock_settings_from_cli.return_value = mock_settings
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
    @patch("previs_builder.Settings.from_cli_args")
    def test_tool_validation_failure(
        self, mock_settings_from_cli: MagicMock, mock_setup_logger: MagicMock, mock_settings: MagicMock  # noqa: ARG002
    ) -> None:
        """Test that the application exits if tool validation fails."""
        mock_settings.tool_paths.validate.return_value = ["xEdit not found"]
        mock_settings_from_cli.return_value = mock_settings

        runner = CliRunner()
        result = runner.invoke(main, ["MyMod.esp"])

        assert result.exit_code == 1
        assert "Tool Configuration Issues" in result.output
        assert "xEdit not found" in result.output
        assert "Cannot proceed without required tools" in result.output

    @patch("previs_builder.setup_logger")
    @patch("previs_builder.sys.platform", "linux")
    @patch("previs_builder.platform.system", return_value="Linux")
    @patch("previs_builder.Settings.from_cli_args")
    @patch("previs_builder.run_build", return_value=True)
    def test_non_windows_warning(
        self, mock_run_build: MagicMock, mock_settings_from_cli: MagicMock, mock_setup_logger: MagicMock, mock_settings: MagicMock  # noqa: ARG002
    ) -> None:
        """Test that a warning is shown on non-Windows platforms."""
        mock_settings_from_cli.return_value = mock_settings

        runner = CliRunner()
        result = runner.invoke(main, ["MyMod.esp"])

        assert result.exit_code == 0
        assert "Running on non-Windows platform" in result.output
        mock_run_build.assert_called_once()

    @patch("previs_builder.setup_logger")
    @patch("previs_builder.Settings.from_cli_args")
    @patch("previs_builder.PrevisBuilder")
    def test_build_cancellation(
        self,
        mock_previs_builder: MagicMock,
        mock_settings_from_cli: MagicMock,
        mock_setup_logger: MagicMock,  # noqa: ARG002
        mock_settings: MagicMock,
        mock_builder: MagicMock,
    ) -> None:
        """Test cancelling the build at the final confirmation."""
        mock_settings_from_cli.return_value = mock_settings
        mock_previs_builder.return_value = mock_builder

        runner = CliRunner()
        # Mocking Confirm.ask to say "no"
        with patch("previs_builder.Confirm.ask", return_value=False):
            result = runner.invoke(main, ["MyMod.esp"])

        # Should exit with code 0 because it's a graceful, user-requested exit
        assert result.exit_code == 0
        assert "Build completed successfully!" not in result.output
        mock_builder.build.assert_not_called()

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
        mock_settings: MagicMock,  # noqa: ARG002
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
        mock_settings: MagicMock,
        mock_builder: MagicMock,
    ) -> None:
        """Test a successful build in fully interactive mode."""
        # Simulate interactive session:
        # 1. Not cleaning up -> False
        # 2. Provide plugin name
        # 3. Select build mode
        # 4. Confirm to proceed with build -> True
        mock_settings.plugin_name = ""  # Start with no plugin
        mock_settings_from_cli.return_value = mock_settings
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
        mock_settings: MagicMock,
        mock_builder: MagicMock,
    ) -> None:
        """Test the build resume flow."""
        mock_builder.failed_step = BuildStep.GENERATE_PRECOMBINED
        mock_settings_from_cli.return_value = mock_settings
        mock_previs_builder.return_value = mock_builder
        mock_prompt_resume.return_value = BuildStep.GENERATE_PRECOMBINED

        runner = CliRunner()
        with patch("previs_builder.Confirm.ask", return_value=True):
            result = runner.invoke(main, ["MyMod.esp"])

        assert result.exit_code == 0
        mock_prompt_resume.assert_called_once()
        mock_builder.build.assert_called_with(start_from_step=BuildStep.GENERATE_PRECOMBINED)

    @patch("previs_builder.setup_logger")
    @patch("previs_builder.Settings.from_cli_args")
    @patch("previs_builder.PrevisBuilder")
    @patch("previs_builder.prompt_for_plugin")
    @patch("previs_builder.prompt_for_cleanup")
    @patch("previs_builder.Confirm.ask")
    def test_interactive_cleanup_flow(  # noqa: PLR0913
        self,
        mock_confirm: MagicMock,
        mock_prompt_cleanup: MagicMock,
        mock_prompt_plugin: MagicMock,
        mock_previs_builder: MagicMock,
        mock_settings_from_cli: MagicMock,
        mock_setup_logger: MagicMock,  # noqa: ARG002
        mock_settings: MagicMock,
        mock_builder: MagicMock,
    ) -> None:
        """Test the interactive cleanup flow."""
        mock_settings.plugin_name = ""  # No plugin to trigger interactive
        mock_settings_from_cli.return_value = mock_settings
        mock_previs_builder.return_value = mock_builder
        mock_prompt_plugin.return_value = "MyOldMod.esp"
        mock_confirm.return_value = True  # Yes to "clean up existing previs files?"

        runner = CliRunner()
        result = runner.invoke(main, [])

        assert result.exit_code == 0
        mock_prompt_plugin.assert_called_once()
        mock_prompt_cleanup.assert_called_with(mock_settings)
        # build should not be called in cleanup mode
        mock_builder.build.assert_not_called()


class TestCommandLineArguments:
    """Test various command-line argument parsing scenarios."""

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
        """Test that CLI arguments are parsed and result in the correct settings."""
        # Create mock tool paths with validation that passes
        mock_tool_paths = ToolPaths(
            creation_kit=Path("/fake/CreationKit.exe"),
            xedit=Path("/fake/FO4Edit.exe"),
            fallout4=Path("/fake/Fallout4.exe"),
            archive2=Path("/fake/Archive2.exe"),
        )
        # Mock validation to return no errors
        mock_tool_paths.validate = MagicMock(return_value=[])  # type: ignore
        mock_tool_discover.return_value = mock_tool_paths

        mock_run_build.return_value = True

        runner = CliRunner()
        result = runner.invoke(main, cli_args, catch_exceptions=False)

        assert result.exit_code == 0, f"CLI crashed with args: {cli_args}"
        mock_run_build.assert_called_once()
        called_settings = mock_run_build.call_args[0][0]

        assert called_settings.plugin_name == expected_plugin
        assert called_settings.build_mode == expected_mode
        # Check archive_tool instead of use_bsarch
        expected_archive_tool = ArchiveTool.BSARCH if expected_bsarch else ArchiveTool.ARCHIVE2
        assert called_settings.archive_tool == expected_archive_tool

    @patch("previs_builder.setup_logger")
    @patch("previs_builder.run_build")
    @patch("PrevisLib.config.settings.find_tool_paths")
    def test_path_overrides(self, mock_tool_discover: MagicMock, mock_run_build: MagicMock, mock_setup_logger: MagicMock) -> None:  # noqa: ARG002
        """Test that --fallout4-path and --xedit-path are passed correctly."""
        # Create mock tool paths with validation that passes
        mock_tool_paths = ToolPaths(
            creation_kit=Path("/fake/CreationKit.exe"),
            xedit=Path("/fake/FO4Edit.exe"),
            fallout4=Path("/fake/Fallout4.exe"),
            archive2=Path("/fake/Archive2.exe"),
        )
        mock_tool_paths.validate = MagicMock(return_value=[])  # type: ignore
        mock_tool_discover.return_value = mock_tool_paths

        mock_run_build.return_value = True

        runner = CliRunner()
        with runner.isolated_filesystem():
            fo4_path = Path("fo4")
            fo4_path.mkdir()
            # Create Fallout4.exe in the fo4 directory
            fo4_exe = fo4_path / "Fallout4.exe"
            fo4_exe.touch()

            xedit_path = Path("fo4edit.exe")
            xedit_path.touch()

            result = runner.invoke(
                main,
                [
                    "--fallout4-path",
                    str(fo4_path),
                    "--xedit-path",
                    str(xedit_path),
                    "MyPlugin.esp",
                ],
                catch_exceptions=False,
            )

        assert result.exit_code == 0
        mock_run_build.assert_called_once()
        called_settings = mock_run_build.call_args[0][0]
        # Compare the paths by resolving both since CLI paths may be stored as relative
        assert called_settings.tool_paths.fallout4.resolve() == fo4_exe.resolve()
        assert called_settings.tool_paths.xedit.resolve() == xedit_path.resolve()
