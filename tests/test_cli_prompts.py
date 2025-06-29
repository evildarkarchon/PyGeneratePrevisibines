"""Tests for CLI prompts and interactive functions in previs_builder."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from previs_builder import (
    prompt_for_build_mode,
    prompt_for_cleanup,
    prompt_for_plugin,
    prompt_for_resume,
)
from PrevisLib.models.data_classes import BuildMode, BuildStep
from PrevisLib.utils.validation import create_plugin_from_template


class TestPluginCreation:
    """Test plugin creation from template."""

    def test_create_plugin_from_template_success(self, tmp_path):
        """Test successful plugin creation from template."""
        # Create mock data directory with template
        data_path = tmp_path / "Data"
        data_path.mkdir()
        template_file = data_path / "xPrevisPatch.esp"
        template_file.write_text("template content")

        success, message = create_plugin_from_template(data_path, "MyMod.esp")

        assert success is True
        assert "Created MyMod.esp from xPrevisPatch.esp template" in message
        assert (data_path / "MyMod.esp").exists()
        assert (data_path / "MyMod.esp").read_text() == "template content"

    def test_create_plugin_from_template_no_template(self, tmp_path):
        """Test plugin creation when template doesn't exist."""
        data_path = tmp_path / "Data"
        data_path.mkdir()

        success, message = create_plugin_from_template(data_path, "MyMod.esp")

        assert success is False
        assert "Template file xPrevisPatch.esp not found" in message

    def test_create_plugin_from_template_copy_error(self, tmp_path):
        """Test plugin creation when copy fails."""
        data_path = tmp_path / "Data"
        data_path.mkdir()
        template_file = data_path / "xPrevisPatch.esp"
        template_file.write_text("template content")

        with patch("shutil.copy2", side_effect=Exception("Copy failed")):
            success, message = create_plugin_from_template(data_path, "MyMod.esp")

        assert success is False
        assert "Failed to create" in message
        assert "Copy failed" in message


class TestPromptForPlugin:
    """Test plugin name prompting."""

    @patch("previs_builder.Prompt.ask")
    def test_prompt_for_plugin_valid_name(self, mock_prompt):
        """Test prompting with a valid plugin name."""
        mock_prompt.return_value = "MyMod.esp"
        
        result = prompt_for_plugin()
        
        assert result == "MyMod.esp"
        mock_prompt.assert_called_once()

    @patch("previs_builder.Prompt.ask")
    @patch("previs_builder.console")
    def test_prompt_for_plugin_empty_name(self, mock_console, mock_prompt):
        """Test prompting with empty name then valid name."""
        mock_prompt.side_effect = ["", "MyMod.esp"]
        
        result = prompt_for_plugin()
        
        assert result == "MyMod.esp"
        assert mock_prompt.call_count == 2
        mock_console.print.assert_any_call("[red]Plugin name cannot be empty. Please enter a valid plugin name.[/red]")

    @patch("previs_builder.validate_plugin_name")
    @patch("previs_builder.Prompt.ask")
    @patch("previs_builder.console")
    def test_prompt_for_plugin_invalid_name(self, mock_console, mock_prompt, mock_validate):
        """Test prompting with invalid name then valid name."""
        mock_prompt.side_effect = ["Invalid@Plugin.esp", "MyMod.esp"]
        mock_validate.side_effect = [(False, "Invalid character"), (True, "")]
        
        result = prompt_for_plugin()
        
        assert result == "MyMod.esp"
        assert mock_prompt.call_count == 2
        # Check that error was printed
        assert any("[red]Error:[/red]" in str(call) for call in mock_console.print.call_args_list)

    @patch("previs_builder.Prompt.ask")
    @patch("previs_builder.console")
    def test_prompt_for_plugin_reserved_name(self, mock_console, mock_prompt):
        """Test prompting with reserved name."""
        mock_prompt.side_effect = ["previs.esp", "MyMod.esp"]
        
        result = prompt_for_plugin()
        
        assert result == "MyMod.esp"
        assert mock_prompt.call_count == 2
        mock_console.print.assert_any_call(
            "\n[red]Error:[/red] Plugin name 'previs' is reserved for internal use. Please choose another."
        )

    @patch("previs_builder.Prompt.ask")
    @patch("previs_builder.Confirm.ask")
    @patch("previs_builder.console")
    def test_prompt_for_plugin_nonexistent_create_yes(self, mock_console, mock_confirm, mock_prompt, tmp_path):
        """Test prompting for non-existent plugin and creating it."""
        mock_prompt.return_value = "NewMod.esp"
        mock_confirm.return_value = True
        
        # Create mock settings with tool paths
        mock_settings = MagicMock()
        mock_settings.tool_paths.fallout4 = tmp_path
        
        # Create template
        data_path = tmp_path / "Data"
        data_path.mkdir()
        template_file = data_path / "xPrevisPatch.esp"
        template_file.write_text("template")
        
        result = prompt_for_plugin(mock_settings)
        
        assert result == "NewMod.esp"
        mock_confirm.assert_called_with("Create it from xPrevisPatch.esp?", default=True)
        assert (data_path / "NewMod.esp").exists()

    @patch("previs_builder.Prompt.ask")
    @patch("previs_builder.Confirm.ask")
    @patch("previs_builder.console")
    def test_prompt_for_plugin_nonexistent_create_no(self, mock_console, mock_confirm, mock_prompt, tmp_path):
        """Test prompting for non-existent plugin and declining to create."""
        mock_prompt.side_effect = ["NewMod.esp", "ExistingMod.esp"]
        mock_confirm.return_value = False
        
        # Create mock settings
        mock_settings = MagicMock()
        mock_settings.tool_paths.fallout4 = tmp_path
        
        # Create data directory
        data_path = tmp_path / "Data"
        data_path.mkdir()
        
        # Create existing plugin
        existing_plugin = data_path / "ExistingMod.esp"
        existing_plugin.write_text("existing")
        
        result = prompt_for_plugin(mock_settings)
        
        assert result == "ExistingMod.esp"
        mock_confirm.assert_called_once()
        mock_console.print.assert_any_call("[dim]Please enter a different plugin name or create the plugin manually.[/dim]")


class TestPromptForBuildMode:
    """Test build mode prompting."""

    @patch("previs_builder.Prompt.ask")
    @patch("previs_builder.console")
    def test_prompt_for_build_mode_clean(self, mock_console, mock_prompt):
        """Test selecting clean build mode."""
        mock_prompt.return_value = "1"
        
        result = prompt_for_build_mode()
        
        assert result == BuildMode.CLEAN
        mock_prompt.assert_called_with("\nSelect mode", choices=["1", "2", "3"], default="1")

    @patch("previs_builder.Prompt.ask")
    def test_prompt_for_build_mode_filtered(self, mock_prompt):
        """Test selecting filtered build mode."""
        mock_prompt.return_value = "2"
        
        result = prompt_for_build_mode()
        
        assert result == BuildMode.FILTERED

    @patch("previs_builder.Prompt.ask")
    def test_prompt_for_build_mode_xbox(self, mock_prompt):
        """Test selecting xbox build mode."""
        mock_prompt.return_value = "3"
        
        result = prompt_for_build_mode()
        
        assert result == BuildMode.XBOX


class TestPromptForResume:
    """Test resume prompting."""

    @patch("previs_builder.Prompt.ask")
    @patch("previs_builder.console")
    def test_prompt_for_resume_start_fresh(self, mock_console, mock_prompt):
        """Test selecting to start fresh."""
        mock_prompt.return_value = "0"
        mock_builder = MagicMock()
        mock_builder.get_resume_options.return_value = [BuildStep.GENERATE_PRECOMBINED, BuildStep.GENERATE_PREVIS]
        
        result = prompt_for_resume(mock_builder)
        
        assert result is None

    @patch("previs_builder.Prompt.ask")
    @patch("previs_builder.console")
    def test_prompt_for_resume_select_step(self, mock_console, mock_prompt):
        """Test selecting a specific step to resume from."""
        mock_prompt.return_value = "2"
        mock_builder = MagicMock()
        mock_builder.get_resume_options.return_value = [BuildStep.GENERATE_PRECOMBINED, BuildStep.GENERATE_PREVIS]
        
        result = prompt_for_resume(mock_builder)
        
        assert result == BuildStep.GENERATE_PREVIS


class TestPromptForCleanup:
    """Test cleanup prompting."""

    @patch("previs_builder.PrevisBuilder")
    @patch("previs_builder.Confirm.ask")
    @patch("previs_builder.console")
    def test_prompt_for_cleanup_confirmed(self, mock_console, mock_confirm, mock_builder_class):
        """Test cleanup prompt when user confirms."""
        mock_settings = MagicMock()
        mock_settings.plugin_name = "TestPlugin.esp"
        
        mock_builder = MagicMock()
        mock_builder.cleanup.return_value = True
        mock_builder_class.return_value = mock_builder
        
        mock_confirm.return_value = True
        
        result = prompt_for_cleanup(mock_settings)
        
        assert result is True
        mock_builder.cleanup.assert_called_once()
        # Verify success message was printed
        assert any("Cleanup completed successfully!" in str(call) for call in mock_console.print.call_args_list)

    @patch("previs_builder.PrevisBuilder")
    @patch("previs_builder.Confirm.ask")
    @patch("previs_builder.console")
    def test_prompt_for_cleanup_declined(self, mock_console, mock_confirm, mock_builder_class):
        """Test cleanup prompt when user declines."""
        mock_settings = MagicMock()
        mock_settings.plugin_name = "TestPlugin.esp"
        
        mock_confirm.return_value = False
        
        result = prompt_for_cleanup(mock_settings)
        
        assert result is False
        mock_builder_class.assert_not_called()

    @patch("previs_builder.PrevisBuilder")
    @patch("previs_builder.Confirm.ask")
    @patch("previs_builder.console")
    def test_prompt_for_cleanup_failed(self, mock_console, mock_confirm, mock_builder_class):
        """Test cleanup prompt when cleanup fails."""
        mock_settings = MagicMock()
        mock_settings.plugin_name = "TestPlugin.esp"
        
        mock_builder = MagicMock()
        mock_builder.cleanup.return_value = False
        mock_builder_class.return_value = mock_builder
        
        mock_confirm.return_value = True
        
        result = prompt_for_cleanup(mock_settings)
        
        assert result is False
        # Verify error message was printed
        assert any("Some files could not be deleted" in str(call) for call in mock_console.print.call_args_list)