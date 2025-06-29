"""Main CLI tests for previs_builder."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from previs_builder import main
from PrevisLib.models.data_classes import BuildMode, BuildStep, ToolPaths


@pytest.fixture
def mock_settings():
    """Fixture to provide a mock Settings object."""
    settings = MagicMock()
    settings.plugin_name = "MyTestPlugin.esp"
    settings.build_mode = BuildMode.CLEAN
    settings.archive_tool.value = "Archive2"
    settings.ckpe_config = None
    settings.tool_paths.validate.return_value = []
    return settings


@pytest.fixture
def mock_builder():
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
        self, mock_previs_builder, mock_settings_from_cli, mock_setup_logger, mock_settings, mock_builder
    ):
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
    def test_tool_validation_failure(self, mock_settings_from_cli, mock_setup_logger, mock_settings):
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
    def test_non_windows_warning(self, mock_run_build, mock_settings_from_cli, mock_setup_logger, mock_settings):
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
    def test_build_cancellation(self, mock_previs_builder, mock_settings_from_cli, mock_setup_logger, mock_settings, mock_builder):
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
    def test_help_message(self, mock_setup_logger):
        """Test that the --help message is displayed correctly."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Usage: main [OPTIONS] [ARGS]..." in result.output
        assert "Automated previs generation for Fallout 4" in result.output

    @patch("previs_builder.setup_logger")
    @patch("previs_builder.Settings.from_cli_args")
    @patch("previs_builder.PrevisBuilder")
    def test_keyboard_interrupt_handling(self, mock_previs_builder, mock_settings_from_cli, mock_setup_logger, mock_settings):
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
    def test_successful_build_interactive(
        self,
        mock_confirm,
        mock_prompt_build_mode,
        mock_prompt_plugin,
        mock_previs_builder,
        mock_settings_from_cli,
        mock_setup_logger,
        mock_settings,
        mock_builder,
    ):
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
    def test_resume_build_flow(
        self,
        mock_prompt_resume,
        mock_previs_builder,
        mock_settings_from_cli,
        mock_setup_logger,
        mock_settings,
        mock_builder,
    ):
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
    def test_interactive_cleanup_flow(
        self,
        mock_confirm,
        mock_prompt_cleanup,
        mock_prompt_plugin,
        mock_previs_builder,
        mock_settings_from_cli,
        mock_setup_logger,
        mock_settings,
        mock_builder,
    ):
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
