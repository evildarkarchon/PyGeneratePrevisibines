"""Tests for command line interface."""

from previs_builder import parse_command_line
from PrevisLib.models.data_classes import BuildMode


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
