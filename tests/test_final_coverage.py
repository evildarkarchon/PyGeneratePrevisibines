"""Final tests to reach 85% coverage target."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from previs_builder import prompt_for_plugin, run_build
from PrevisLib.config.settings import Settings
from PrevisLib.models.data_classes import BuildMode, BuildStep, ToolPaths


class TestFinalCoverage:
    """Tests to cover the final missing lines."""

    @patch("previs_builder.Prompt.ask")
    @patch("previs_builder.console")
    def test_prompt_for_plugin_with_valid_name_on_second_try(self, mock_console, mock_prompt):
        """Test prompt_for_plugin with valid name after space in first attempt."""
        mock_prompt.side_effect = ["  ", "ValidPlugin.esp"]  # Spaces first, then valid
        
        result = prompt_for_plugin()
        
        assert result == "ValidPlugin.esp"
        assert mock_prompt.call_count == 2
        # Should print error about empty name
        assert any("[red]Plugin name cannot be empty" in str(call) for call in mock_console.print.call_args_list)

    @patch("previs_builder.PrevisBuilder")
    @patch("previs_builder.Confirm.ask")
    @patch("previs_builder.console")
    @patch("previs_builder.Progress")
    def test_run_build_with_progress_updates(self, mock_progress_class, mock_console, mock_confirm, mock_builder_class):
        """Test run_build with progress tracking."""
        # Setup
        mock_settings = MagicMock()
        mock_builder = MagicMock()
        mock_builder.failed_step = None
        mock_builder.build.return_value = True
        mock_builder._get_steps.return_value = [BuildStep.GENERATE_PRECOMBINED]
        mock_builder_class.return_value = mock_builder
        
        # Mock progress
        mock_progress = MagicMock()
        mock_task = MagicMock()
        mock_progress.add_task.return_value = mock_task
        mock_progress_class.return_value = mock_progress
        
        mock_confirm.return_value = True
        
        # Execute
        result = run_build(mock_settings)
        
        assert result is True
        # Progress should be updated
        mock_progress.update.assert_called()

    @patch("previs_builder.Prompt.ask")
    @patch("previs_builder.Confirm.ask")
    @patch("previs_builder.console")  
    def test_prompt_for_plugin_template_creation_failed(self, mock_console, mock_confirm, mock_prompt, tmp_path):
        """Test plugin prompt when template creation fails."""
        mock_prompt.side_effect = ["NewPlugin.esp", "ExistingPlugin.esp"]
        mock_confirm.return_value = True
        
        # Setup settings
        mock_settings = MagicMock()
        mock_settings.tool_paths.fallout4 = tmp_path
        
        # Create data directory but no template
        data_path = tmp_path / "Data"
        data_path.mkdir()
        (data_path / "ExistingPlugin.esp").touch()
        
        result = prompt_for_plugin(mock_settings)
        
        assert result == "ExistingPlugin.esp"
        assert mock_prompt.call_count == 2

    @patch("previs_builder.Prompt.ask")
    def test_prompt_for_plugin_xbox_reserved_name(self, mock_prompt):
        """Test prompting with xbox reserved name (combinedobjects)."""
        mock_prompt.side_effect = ["CombinedObjects.esp", "MyMod.esp"]
        
        result = prompt_for_plugin()
        
        assert result == "MyMod.esp"
        assert mock_prompt.call_count == 2


class TestInteractiveCleanupScenario:
    """Test specific interactive cleanup scenario."""

    @patch("previs_builder.setup_logger")
    @patch("previs_builder.Settings.from_cli_args")
    @patch("previs_builder.PrevisBuilder")
    @patch("previs_builder.prompt_for_plugin")
    @patch("previs_builder.Confirm.ask")
    @patch("previs_builder.console")
    def test_main_interactive_cleanup_success_then_exit(
        self,
        mock_console,
        mock_confirm,
        mock_prompt_plugin,
        mock_builder_class,
        mock_settings_from_cli,
        mock_setup_logger
    ):
        """Test interactive mode: cleanup success, then exit without build."""
        # Setup
        mock_settings = MagicMock()
        mock_settings.plugin_name = ""
        mock_settings.tool_paths.validate.return_value = []
        mock_settings_from_cli.return_value = mock_settings
        
        mock_builder = MagicMock()
        mock_builder.cleanup.return_value = True
        mock_builder_class.return_value = mock_builder
        
        mock_prompt_plugin.return_value = "Cleaned.esp"
        mock_confirm.side_effect = [True]  # Yes to cleanup only
        
        # Import and run
        from previs_builder import main
        from click.testing import CliRunner
        
        runner = CliRunner()
        result = runner.invoke(main, [])
        
        assert result.exit_code == 0
        mock_builder.cleanup.assert_called_once()