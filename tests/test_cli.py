"""Tests for command line interface."""

from pathlib import Path
from unittest.mock import patch

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


class TestCLIPathOverrides:
    """Test CLI path override functionality."""

    @patch("PrevisLib.config.settings.find_tool_paths")
    def test_fallout4_path_override(self, mock_find_tools):
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
        def mock_exists(self):
            return self in [fake_fo4_exe, fake_ck_exe, fake_archive_exe]

        with patch.object(Path, "exists", mock_exists):
            # Test the override
            settings = Settings.from_cli_args(fallout4_path=fake_fo4_path)

            assert settings.tool_paths.fallout4 == fake_fo4_exe
            assert settings.tool_paths.creation_kit == fake_ck_exe
            assert settings.tool_paths.archive2 == fake_archive_exe

    @patch("PrevisLib.config.settings.find_tool_paths")
    def test_xedit_path_override(self, mock_find_tools):
        """Test that --xedit-path correctly overrides tool discovery."""
        # Mock the default tool discovery
        mock_tool_paths = ToolPaths()
        mock_find_tools.return_value = mock_tool_paths

        # Create a fake xEdit path
        fake_xedit_path = Path("/fake/tools/FO4Edit.exe")
        fake_bsarch_path = fake_xedit_path.parent / "BSArch.exe"

        # Mock file existence by patching the exists method to return True for our test paths
        def mock_exists(self):
            return self in [fake_xedit_path, fake_bsarch_path]

        with patch.object(Path, "exists", mock_exists):
            # Test the override
            settings = Settings.from_cli_args(xedit_path=fake_xedit_path)

            assert settings.tool_paths.xedit == fake_xedit_path
            assert settings.tool_paths.bsarch == fake_bsarch_path

    @patch("PrevisLib.config.settings.find_tool_paths")
    def test_fallout4_path_missing_exe_raises_error(self, mock_find_tools):
        """Test that missing Fallout4.exe in specified path raises error."""
        mock_tool_paths = ToolPaths()
        mock_find_tools.return_value = mock_tool_paths

        fake_fo4_path = Path("/fake/fallout4")

        with patch.object(Path, "exists", return_value=False):
            with pytest.raises(ValueError, match="Fallout4.exe not found in specified path"):
                Settings.from_cli_args(fallout4_path=fake_fo4_path)

    @patch("PrevisLib.config.settings.find_tool_paths")
    def test_combined_path_overrides(self, mock_find_tools):
        """Test using both --fallout4-path and --xedit-path together."""
        mock_tool_paths = ToolPaths()
        mock_find_tools.return_value = mock_tool_paths

        fake_fo4_path = Path("/fake/fallout4")
        fake_fo4_exe = fake_fo4_path / "Fallout4.exe"
        fake_ck_exe = fake_fo4_path / "CreationKit.exe"

        fake_xedit_path = Path("/different/tools/FO4Edit.exe")

        # Mock file existence by patching the exists method to return True for our test paths
        def mock_exists(self):
            return self in [fake_fo4_exe, fake_ck_exe, fake_xedit_path]

        with patch.object(Path, "exists", mock_exists):
            settings = Settings.from_cli_args(fallout4_path=fake_fo4_path, xedit_path=fake_xedit_path)

            assert settings.tool_paths.fallout4 == fake_fo4_exe
            assert settings.tool_paths.creation_kit == fake_ck_exe
            assert settings.tool_paths.xedit == fake_xedit_path


class TestPluginPrompting:
    """Test plugin name prompting functionality."""

    @patch("previs_builder.Prompt.ask")
    @patch("previs_builder.Confirm.ask")
    def test_prompt_for_plugin_exit(self, mock_confirm, mock_prompt):
        """Test exiting plugin prompt with KeyboardInterrupt."""
        mock_prompt.side_effect = KeyboardInterrupt()
        mock_confirm.return_value = True

        with pytest.raises(KeyboardInterrupt):
            prompt_for_plugin()

    @patch("previs_builder.Prompt.ask")
    @patch("previs_builder.console.print")
    def test_prompt_for_plugin_validation_error(self, mock_print, mock_prompt):
        """Test plugin validation error handling."""
        # First call returns invalid name, second call raises KeyboardInterrupt to exit
        mock_prompt.side_effect = ["invalid name with spaces", KeyboardInterrupt()]

        with patch("previs_builder.Confirm.ask", return_value=True):
            with pytest.raises(KeyboardInterrupt):
                prompt_for_plugin()

        # Should have printed an error about spaces
        mock_print.assert_any_call("\n[red]Error:[/red] Plugin name cannot contain spaces")

    @patch("previs_builder.validate_plugin_name")
    @patch("previs_builder.Prompt.ask")
    def test_prompt_for_plugin_valid_name(self, mock_prompt, mock_validate):
        """Test successful plugin name validation."""
        mock_prompt.return_value = "TestMod.esp"
        mock_validate.return_value = (True, "")

        result = prompt_for_plugin()
        assert result == "TestMod.esp"


class TestModernCLIArguments:
    """Test modern Click-style CLI arguments."""

    @patch("PrevisLib.config.settings.find_tool_paths")
    def test_modern_build_mode_argument(self, mock_find_tools):
        """Test --build-mode argument."""
        mock_tool_paths = ToolPaths()
        mock_find_tools.return_value = mock_tool_paths

        # Test each build mode
        for mode in ["clean", "filtered", "xbox"]:
            settings = Settings.from_cli_args(plugin_name="TestMod.esp", build_mode=mode)
            assert settings.build_mode.value == mode

    @patch("PrevisLib.config.settings.find_tool_paths")
    def test_modern_archive_tool_argument(self, mock_find_tools):
        """Test --archive-tool argument."""
        mock_tool_paths = ToolPaths()
        mock_find_tools.return_value = mock_tool_paths

        # Test archive2 (default)
        settings = Settings.from_cli_args(use_bsarch=False)
        assert settings.archive_tool.value == "Archive2"

        # Test bsarch
        settings = Settings.from_cli_args(use_bsarch=True)
        assert settings.archive_tool.value == "BSArch"

    @patch("PrevisLib.config.settings.find_tool_paths")
    def test_modern_plugin_argument(self, mock_find_tools):
        """Test --plugin argument."""
        mock_tool_paths = ToolPaths()
        mock_find_tools.return_value = mock_tool_paths

        settings = Settings.from_cli_args(plugin_name="MyMod.esp")
        assert settings.plugin_name == "MyMod.esp"

    @patch("PrevisLib.config.settings.find_tool_paths")
    def test_modern_verbose_argument(self, mock_find_tools):
        """Test --verbose argument."""
        mock_tool_paths = ToolPaths()
        mock_find_tools.return_value = mock_tool_paths

        settings = Settings.from_cli_args(verbose=True)
        assert settings.verbose is True

        settings = Settings.from_cli_args(verbose=False)
        assert settings.verbose is False

    @patch("PrevisLib.config.settings.find_tool_paths")
    def test_combined_modern_arguments(self, mock_find_tools):
        """Test multiple modern arguments together."""
        mock_tool_paths = ToolPaths()
        mock_find_tools.return_value = mock_tool_paths

        settings = Settings.from_cli_args(plugin_name="TestMod.esp", build_mode="filtered", use_bsarch=True, verbose=True)

        assert settings.plugin_name == "TestMod.esp"
        assert settings.build_mode.value == "filtered"
        assert settings.archive_tool.value == "BSArch"
        assert settings.verbose is True


class TestBackwardCompatibility:
    """Test that legacy and modern arguments work together."""

    @patch("PrevisLib.config.settings.find_tool_paths")
    def test_legacy_arguments_still_work(self, mock_find_tools):
        """Test that legacy batch-file style arguments still work."""
        mock_tool_paths = ToolPaths()
        mock_find_tools.return_value = mock_tool_paths

        # Simulate how the main function would process legacy args
        legacy_plugin, legacy_mode, legacy_bsarch = parse_command_line(["-filtered", "-bsarch", "TestMod.esp"])

        # This is how main() processes them
        final_plugin = None or legacy_plugin  # No modern --plugin specified
        final_build_mode = None or (legacy_mode.value if legacy_mode else None)  # No modern --build-mode
        final_use_bsarch = False if None else legacy_bsarch  # No modern --archive-tool

        settings = Settings.from_cli_args(plugin_name=final_plugin, build_mode=final_build_mode, use_bsarch=final_use_bsarch)

        assert settings.plugin_name == "TestMod.esp"
        assert settings.build_mode.value == "filtered"
        assert settings.archive_tool.value == "BSArch"

    @patch("PrevisLib.config.settings.find_tool_paths")
    def test_modern_arguments_override_legacy(self, mock_find_tools):
        """Test that modern arguments take precedence over legacy ones."""
        mock_tool_paths = ToolPaths()
        mock_find_tools.return_value = mock_tool_paths

        # Simulate conflicting legacy and modern args
        legacy_plugin, legacy_mode, legacy_bsarch = parse_command_line(["-clean", "OldMod.esp"])

        # Modern args should take precedence
        modern_plugin = "NewMod.esp"
        modern_build_mode = "xbox"
        modern_archive_tool = "bsarch"

        # This is how main() would merge them
        final_plugin = modern_plugin or legacy_plugin
        final_build_mode = modern_build_mode or (legacy_mode.value if legacy_mode else None)
        final_use_bsarch = (modern_archive_tool == "bsarch") if modern_archive_tool else legacy_bsarch

        settings = Settings.from_cli_args(plugin_name=final_plugin, build_mode=final_build_mode, use_bsarch=final_use_bsarch)

        # Modern values should win
        assert settings.plugin_name == "NewMod.esp"
        assert settings.build_mode.value == "xbox"
        assert settings.archive_tool.value == "BSArch"
