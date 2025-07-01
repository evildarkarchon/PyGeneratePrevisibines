"""Tests for BSArch CLI enhancement functionality."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from PrevisLib.config.settings import Settings
from PrevisLib.models.data_classes import ArchiveTool, ToolPaths


class TestBSArchCLIEnhancement:
    """Test BSArch CLI path functionality."""

    @pytest.fixture
    def mock_paths(self, tmp_path: Path) -> dict[str, Path]:
        """Create mock paths for testing."""
        fallout4_exe = tmp_path / "Fallout4.exe"
        xedit_exe = tmp_path / "FO4Edit.exe"
        bsarch_exe = tmp_path / "BSArch.exe"

        # Create the files
        fallout4_exe.touch()
        xedit_exe.touch()
        bsarch_exe.touch()

        return {
            "fallout4": fallout4_exe,
            "xedit": xedit_exe,
            "bsarch": bsarch_exe,
        }

    def test_from_cli_args_with_bsarch_path(self, mock_paths: dict[str, Path]) -> None:
        """Test Settings.from_cli_args with BSArch path parameter."""
        with patch("PrevisLib.config.settings.find_tool_paths") as mock_find_tools:
            mock_find_tools.return_value = ToolPaths()

            settings = Settings.from_cli_args(
                plugin_name="TestMod.esp",
                bsarch_path=mock_paths["bsarch"],
            )

            assert settings.tool_paths.bsarch == mock_paths["bsarch"]
            assert settings.plugin_name == "TestMod.esp"

    def test_bsarch_path_overrides_auto_discovery(self, mock_paths: dict[str, Path]) -> None:
        """Test that CLI BSArch path overrides automatic discovery."""
        # Create an additional BSArch file near xEdit in a different location
        xedit_dir = mock_paths["xedit"].parent / "xedit_tools"
        xedit_dir.mkdir()
        alt_xedit = xedit_dir / "FO4Edit.exe"
        alt_xedit.touch()
        auto_bsarch = xedit_dir / "BSArch.exe"
        auto_bsarch.touch()

        with patch("PrevisLib.config.settings.find_tool_paths") as mock_find_tools:
            mock_find_tools.return_value = ToolPaths()

            settings = Settings.from_cli_args(
                xedit_path=alt_xedit,
                bsarch_path=mock_paths["bsarch"],  # This should take precedence
            )

            # Should use the explicitly provided BSArch path, not the auto-discovered one
            assert settings.tool_paths.bsarch == mock_paths["bsarch"]
            assert settings.tool_paths.bsarch != auto_bsarch

    def test_auto_discovery_when_no_bsarch_path_provided(self, mock_paths: dict[str, Path]) -> None:
        """Test automatic BSArch discovery when no explicit path is provided."""
        # Create BSArch file near xEdit
        auto_bsarch = mock_paths["xedit"].parent / "BSArch.exe"
        auto_bsarch.touch()

        with patch("PrevisLib.config.settings.find_tool_paths") as mock_find_tools:
            mock_find_tools.return_value = ToolPaths()

            settings = Settings.from_cli_args(
                xedit_path=mock_paths["xedit"],
                # No bsarch_path provided
            )

            # Should auto-discover BSArch near xEdit
            assert settings.tool_paths.bsarch == auto_bsarch

    def test_no_auto_discovery_when_bsarch_path_provided(self, mock_paths: dict[str, Path]) -> None:
        """Test that auto-discovery is skipped when BSArch path is explicitly provided."""
        # Create BSArch file near xEdit that should NOT be used
        auto_bsarch = mock_paths["xedit"].parent / "BSArch.exe"
        auto_bsarch.touch()

        with (
            patch("PrevisLib.config.settings.find_tool_paths") as mock_find_tools,
            patch("PrevisLib.config.settings.logger") as mock_logger,
        ):
            mock_find_tools.return_value = ToolPaths()

            Settings.from_cli_args(
                xedit_path=mock_paths["xedit"],
                bsarch_path=mock_paths["bsarch"],
            )

            # Verify that the debug message for auto-discovery was NOT called
            auto_discovery_calls = [call for call in mock_logger.debug.call_args_list if "Found BSArch near xEdit" in str(call)]
            assert len(auto_discovery_calls) == 0

            # Verify that the CLI BSArch path debug message WAS called
            cli_bsarch_calls = [call for call in mock_logger.debug.call_args_list if "Using CLI-specified BSArch path" in str(call)]
            assert len(cli_bsarch_calls) == 1

    def test_bsarch_path_with_archive_tool_preference(self, mock_paths: dict[str, Path]) -> None:
        """Test BSArch path with archive tool preference."""
        with patch("PrevisLib.config.settings.find_tool_paths") as mock_find_tools:
            mock_find_tools.return_value = ToolPaths()

            settings = Settings.from_cli_args(
                plugin_name="TestMod.esp",
                bsarch_path=mock_paths["bsarch"],
                use_bsarch=True,
            )

            assert settings.tool_paths.bsarch == mock_paths["bsarch"]
            assert settings.archive_tool == ArchiveTool.BSARCH

    def test_bsarch_path_none_handling(self) -> None:
        """Test that None BSArch path is handled gracefully."""
        with patch("PrevisLib.config.settings.find_tool_paths") as mock_find_tools:
            mock_find_tools.return_value = ToolPaths()

            settings = Settings.from_cli_args(
                plugin_name="TestMod.esp",
                bsarch_path=None,  # Explicit None
            )

            # Should not crash and BSArch path should remain None
            assert settings.tool_paths.bsarch is None

    def test_logging_for_cli_bsarch_path(self, mock_paths: dict[str, Path]) -> None:
        """Test that proper logging occurs for CLI BSArch path."""
        with (
            patch("PrevisLib.config.settings.find_tool_paths") as mock_find_tools,
            patch("PrevisLib.config.settings.logger") as mock_logger,
        ):
            mock_find_tools.return_value = ToolPaths()

            Settings.from_cli_args(
                bsarch_path=mock_paths["bsarch"],
            )

            # Verify logging call
            mock_logger.debug.assert_any_call(f"Using CLI-specified BSArch path: {mock_paths['bsarch']}")

    def test_bsarch_path_validation_in_tool_paths(self, mock_paths: dict[str, Path]) -> None:
        """Test that BSArch path is properly validated in ToolPaths."""
        # Create xEdit scripts directory to avoid script validation errors
        xedit_scripts_dir = mock_paths["xedit"].parent / "Edit Scripts"
        xedit_scripts_dir.mkdir()

        with patch("PrevisLib.config.settings.find_tool_paths") as mock_find_tools:
            mock_find_tools.return_value = ToolPaths()

            settings = Settings.from_cli_args(
                plugin_name="TestMod.esp",
                fallout4_path=mock_paths["fallout4"].parent,
                xedit_path=mock_paths["xedit"],
                bsarch_path=mock_paths["bsarch"],
            )

            # Validate tools - should not report archive tool as missing since BSArch is available
            errors = settings.validate_tools()
            archive_errors = [error for error in errors if "No archive tool found" in error]

            # BSArch is available, so no "No archive tool found" error should occur
            assert len(archive_errors) == 0

    def test_combined_path_overrides(self, mock_paths: dict[str, Path]) -> None:
        """Test multiple path overrides working together."""
        with patch("PrevisLib.config.settings.find_tool_paths") as mock_find_tools:
            mock_find_tools.return_value = ToolPaths()

            settings = Settings.from_cli_args(
                plugin_name="TestMod.esp",
                fallout4_path=mock_paths["fallout4"].parent,
                xedit_path=mock_paths["xedit"],
                bsarch_path=mock_paths["bsarch"],
                use_bsarch=True,
            )

            assert settings.tool_paths.fallout4 == mock_paths["fallout4"]
            assert settings.tool_paths.xedit == mock_paths["xedit"]
            assert settings.tool_paths.bsarch == mock_paths["bsarch"]
            assert settings.archive_tool == ArchiveTool.BSARCH
            assert settings.plugin_name == "TestMod.esp"


class TestBSArchPathPrecedence:
    """Test BSArch path precedence rules."""

    @pytest.fixture
    def complex_setup(self, tmp_path: Path) -> dict[str, Path]:
        """Create a complex directory setup for precedence testing."""
        # Create various BSArch locations
        cli_bsarch = tmp_path / "cli" / "BSArch.exe"
        xedit_dir = tmp_path / "xedit"
        xedit_exe = xedit_dir / "FO4Edit.exe"
        auto_bsarch = xedit_dir / "BSArch.exe"

        # Create directories and files
        cli_bsarch.parent.mkdir(parents=True)
        xedit_dir.mkdir(parents=True)

        cli_bsarch.touch()
        xedit_exe.touch()
        auto_bsarch.touch()

        return {
            "cli_bsarch": cli_bsarch,
            "xedit": xedit_exe,
            "auto_bsarch": auto_bsarch,
        }

    def test_cli_path_precedence_over_auto_discovery(self, complex_setup: dict[str, Path]) -> None:
        """Test that CLI BSArch path takes precedence over auto-discovery."""
        with patch("PrevisLib.config.settings.find_tool_paths") as mock_find_tools:
            mock_find_tools.return_value = ToolPaths()

            settings = Settings.from_cli_args(
                xedit_path=complex_setup["xedit"],
                bsarch_path=complex_setup["cli_bsarch"],
            )

            # CLI path should win
            assert settings.tool_paths.bsarch == complex_setup["cli_bsarch"]
            assert settings.tool_paths.bsarch != complex_setup["auto_bsarch"]

    def test_auto_discovery_when_cli_not_provided(self, complex_setup: dict[str, Path]) -> None:
        """Test auto-discovery when CLI BSArch path is not provided."""
        with patch("PrevisLib.config.settings.find_tool_paths") as mock_find_tools:
            mock_find_tools.return_value = ToolPaths()

            settings = Settings.from_cli_args(
                xedit_path=complex_setup["xedit"],
                # No bsarch_path provided
            )

            # Auto-discovery should work
            assert settings.tool_paths.bsarch == complex_setup["auto_bsarch"]
