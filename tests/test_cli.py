"""Tests for command line interface."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from previs_builder import parse_command_line, prompt_for_plugin
from PrevisLib.config.settings import Settings
from PrevisLib.models.data_classes import BuildMode, ToolPaths


class TestCommandLineParsing:
    """Test command line argument parsing."""

    def test_empty_args(self):
        """Test parsing with no arguments."""
        plugin, mode, bsarch = parse_command_line([])

        assert plugin is None
        assert mode == BuildMode.CLEAN
        assert bsarch is False

    def test_plugin_only(self):
        """Test parsing with plugin name only."""
        plugin, mode, bsarch = parse_command_line(["TestMod.esp"])

        assert plugin == "TestMod.esp"
        assert mode == BuildMode.CLEAN
        assert bsarch is False

    def test_build_mode_flags(self):
        """Test parsing build mode flags."""
        test_cases = [
            (["-clean"], BuildMode.CLEAN),
            (["-filtered"], BuildMode.FILTERED),
            (["-xbox"], BuildMode.XBOX),
        ]

        for args, expected_mode in test_cases:
            plugin, mode, bsarch = parse_command_line(args)
            assert mode == expected_mode

    def test_bsarch_flag(self):
        """Test parsing BSArch flag."""
        plugin, mode, bsarch = parse_command_line(["-bsarch"])
        assert bsarch is True

    def test_combined_flags(self):
        """Test parsing multiple flags together."""
        plugin, mode, bsarch = parse_command_line(["-filtered", "-bsarch", "TestMod.esp"])

        assert plugin == "TestMod.esp"
        assert mode == BuildMode.FILTERED
        assert bsarch is True

    def test_order_independence(self):
        """Test that argument order doesn't matter."""
        # Test different orderings
        orderings = [
            ["TestMod.esp", "-filtered", "-bsarch"],
            ["-filtered", "TestMod.esp", "-bsarch"],
            ["-bsarch", "-filtered", "TestMod.esp"],
        ]

        for args in orderings:
            plugin, mode, bsarch = parse_command_line(args)
            assert plugin == "TestMod.esp"
            assert mode == BuildMode.FILTERED
            assert bsarch is True

    def test_case_sensitivity(self):
        """Test that flags are case insensitive."""
        plugin, mode, bsarch = parse_command_line(["-FILTERED", "-BSARCH"])

        assert mode == BuildMode.FILTERED
        assert bsarch is True

    def test_multiple_plugins_first_wins(self):
        """Test that only the first plugin name is used."""
        plugin, mode, bsarch = parse_command_line(["First.esp", "Second.esp"])

        assert plugin == "First.esp"

    def test_override_build_mode(self):
        """Test that later build mode flags override earlier ones."""
        plugin, mode, bsarch = parse_command_line(["-clean", "-filtered", "-xbox"])

        # Should use the last one specified
        assert mode == BuildMode.XBOX


class TestPromptForPlugin:
    """Test interactive plugin prompting with template creation."""

    @pytest.fixture
    def mock_settings(self, tmp_path):
        """Create mock settings with temporary paths."""
        fo4_path = tmp_path / "Fallout4"
        fo4_path.mkdir()
        data_path = fo4_path / "Data"
        data_path.mkdir()

        tool_paths = ToolPaths(
            fallout4=fo4_path, creation_kit=fo4_path / "CreationKit.exe", xedit=fo4_path / "xEdit.exe", archive2=fo4_path / "Archive2.exe"
        )

        settings = Settings()
        settings.tool_paths = tool_paths
        return settings

    @patch("previs_builder.Prompt.ask")
    @patch("previs_builder.Confirm.ask")
    def test_prompt_plugin_existing_plugin(self, mock_confirm, mock_prompt, mock_settings):
        """Test prompting when plugin already exists."""
        mock_prompt.return_value = "ExistingMod.esp"

        # Create the plugin file to simulate it exists
        plugin_path = mock_settings.tool_paths.fallout4 / "Data" / "ExistingMod.esp"
        plugin_path.write_text("Existing plugin content")

        result = prompt_for_plugin(mock_settings)

        assert result == "ExistingMod.esp"
        mock_prompt.assert_called_once()
        # Confirm should not be called for existing plugins
        mock_confirm.assert_not_called()

    @patch("previs_builder.Prompt.ask")
    @patch("previs_builder.Confirm.ask")
    @patch("previs_builder.create_plugin_from_template")
    def test_prompt_plugin_create_from_template_accept(self, mock_create, mock_confirm, mock_prompt, mock_settings):
        """Test prompting when plugin doesn't exist and user accepts template creation."""
        mock_prompt.return_value = "NewMod.esp"
        mock_confirm.return_value = True  # User accepts template creation
        mock_create.return_value = (True, "Created NewMod.esp from xPrevisPatch.esp template")

        result = prompt_for_plugin(mock_settings)

        assert result == "NewMod.esp"
        mock_prompt.assert_called_once()
        mock_confirm.assert_called_once()
        mock_create.assert_called_once_with(mock_settings.tool_paths.fallout4 / "Data", "NewMod.esp")

    @patch("previs_builder.Prompt.ask")
    @patch("previs_builder.Confirm.ask")
    @patch("previs_builder.create_plugin_from_template")
    def test_prompt_plugin_create_from_template_decline(self, mock_create, mock_confirm, mock_prompt, mock_settings):
        """Test prompting when plugin doesn't exist and user declines template creation."""
        mock_prompt.side_effect = ["NewMod.esp", "DifferentMod.esp"]
        mock_confirm.return_value = False  # User declines template creation

        # Create the second plugin to avoid infinite loop
        plugin_path = mock_settings.tool_paths.fallout4 / "Data" / "DifferentMod.esp"
        plugin_path.write_text("Different plugin content")

        result = prompt_for_plugin(mock_settings)

        assert result == "DifferentMod.esp"
        assert mock_prompt.call_count == 2
        mock_confirm.assert_called_once()
        mock_create.assert_not_called()

    @patch("previs_builder.Prompt.ask")
    @patch("previs_builder.Confirm.ask")
    @patch("previs_builder.create_plugin_from_template")
    def test_prompt_plugin_template_creation_fails(self, mock_create, mock_confirm, mock_prompt, mock_settings):
        """Test prompting when template creation fails."""
        mock_prompt.side_effect = ["NewMod.esp", "ExistingMod.esp"]
        mock_confirm.return_value = True  # User accepts template creation
        mock_create.return_value = (False, "xPrevisPatch.esp template not found")

        # Create the second plugin to avoid infinite loop
        plugin_path = mock_settings.tool_paths.fallout4 / "Data" / "ExistingMod.esp"
        plugin_path.write_text("Existing plugin content")

        result = prompt_for_plugin(mock_settings)

        assert result == "ExistingMod.esp"
        assert mock_prompt.call_count == 2
        mock_confirm.assert_called_once()
        mock_create.assert_called_once()

    @patch("previs_builder.Prompt.ask")
    @patch("previs_builder.Confirm.ask")
    def test_prompt_plugin_reserved_names(self, mock_confirm, mock_prompt, mock_settings):
        """Test prompting with reserved plugin names."""
        mock_prompt.side_effect = ["previs.esp", "ValidMod.esp"]

        # Create the valid plugin to avoid infinite loop
        plugin_path = mock_settings.tool_paths.fallout4 / "Data" / "ValidMod.esp"
        plugin_path.write_text("Valid plugin content")

        result = prompt_for_plugin(mock_settings)

        assert result == "ValidMod.esp"
        assert mock_prompt.call_count == 2

    @patch("previs_builder.Prompt.ask")
    @patch("previs_builder.Confirm.ask")
    def test_prompt_plugin_xprevispatch_special_case(self, mock_confirm, mock_prompt, mock_settings):
        """Test prompting with xPrevisPatch.esp special case."""
        mock_prompt.side_effect = ["xprevispatch.esp", "ValidMod.esp"]
        mock_confirm.return_value = True  # User wants to use different name

        # Create the valid plugin to avoid infinite loop
        plugin_path = mock_settings.tool_paths.fallout4 / "Data" / "ValidMod.esp"
        plugin_path.write_text("Valid plugin content")

        result = prompt_for_plugin(mock_settings)

        assert result == "ValidMod.esp"
        assert mock_prompt.call_count == 2
        mock_confirm.assert_called_once()

    @patch("previs_builder.Prompt.ask")
    @patch("previs_builder.Confirm.ask")
    def test_prompt_plugin_no_settings(self, mock_confirm, mock_prompt):
        """Test prompting without settings (no template creation available)."""
        mock_prompt.return_value = "SomeMod.esp"

        result = prompt_for_plugin(None)

        assert result == "SomeMod.esp"
        mock_prompt.assert_called_once()
        # Should not try to check if plugin exists or create template
        mock_confirm.assert_not_called()
