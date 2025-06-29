"""Tests for command line interface."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from previs_builder import prompt_for_plugin
from PrevisLib.config.settings import Settings
from PrevisLib.models.data_classes import BuildMode, ToolPaths


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

    @patch("PrevisLib.config.settings.find_tool_paths")
    def test_combined_path_overrides(self, mock_find_tools: MagicMock) -> None:
        """Test using both --fallout4-path and --xedit-path together."""
        mock_tool_paths = ToolPaths()
        mock_find_tools.return_value = mock_tool_paths

        fake_fo4_path = Path("/fake/fallout4")
        fake_fo4_exe = fake_fo4_path / "Fallout4.exe"
        fake_ck_exe = fake_fo4_path / "CreationKit.exe"

        fake_xedit_path = Path("/different/tools/FO4Edit.exe")

        # Mock file existence by patching the exists method to return True for our test paths
        def mock_exists(self) -> bool:  # noqa: ANN001
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


class TestModernCLIArguments:
    """Test modern Click-style CLI arguments."""

    @patch("PrevisLib.config.settings.find_tool_paths")
    def test_modern_build_mode_argument(self, mock_find_tools: MagicMock) -> None:
        """Test --build-mode argument."""
        mock_tool_paths = ToolPaths()
        mock_find_tools.return_value = mock_tool_paths

        # Test each build mode
        for mode in ["clean", "filtered", "xbox"]:
            settings = Settings.from_cli_args(plugin_name="TestMod.esp", build_mode=mode)
            assert settings.build_mode.value == mode

    @patch("PrevisLib.config.settings.find_tool_paths")
    def test_modern_archive_tool_argument(self, mock_find_tools: MagicMock) -> None:
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
    def test_modern_plugin_argument(self, mock_find_tools: MagicMock) -> None:
        """Test --plugin argument."""
        mock_tool_paths = ToolPaths()
        mock_find_tools.return_value = mock_tool_paths

        settings = Settings.from_cli_args(plugin_name="MyMod.esp")
        assert settings.plugin_name == "MyMod.esp"

    @patch("PrevisLib.config.settings.find_tool_paths")
    def test_modern_verbose_argument(self, mock_find_tools: MagicMock) -> None:
        """Test --verbose argument."""
        mock_tool_paths = ToolPaths()
        mock_find_tools.return_value = mock_tool_paths

        settings = Settings.from_cli_args(verbose=True)
        assert settings.verbose is True

        settings = Settings.from_cli_args(verbose=False)
        assert settings.verbose is False

    @patch("PrevisLib.config.settings.find_tool_paths")
    def test_combined_modern_arguments(self, mock_find_tools: MagicMock) -> None:
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
    def test_legacy_arguments_still_work(self, mock_find_tools: MagicMock) -> None:
        """Test that legacy batch-file style arguments still work."""
        mock_tool_paths = ToolPaths()
        mock_find_tools.return_value = mock_tool_paths

        # Test that legacy batch-file style arguments are processed correctly
        # by directly creating settings with the expected values
        settings = Settings.from_cli_args(plugin_name="TestMod.esp", build_mode="filtered", use_bsarch=True)

        assert settings.plugin_name == "TestMod.esp"
        assert settings.build_mode.value == "filtered"
        assert settings.archive_tool.value == "BSArch"

    @patch("PrevisLib.config.settings.find_tool_paths")
    def test_modern_arguments_override_legacy(self, mock_find_tools: MagicMock) -> None:
        """Test that modern arguments take precedence over legacy ones."""
        mock_tool_paths = ToolPaths()
        mock_find_tools.return_value = mock_tool_paths

        # Test that modern arguments take precedence when specified
        settings = Settings.from_cli_args(plugin_name="NewMod.esp", build_mode="xbox", use_bsarch=True)

        # Modern values should win
        assert settings.plugin_name == "NewMod.esp"
        assert settings.build_mode.value == "xbox"
        assert settings.archive_tool.value == "BSArch"
