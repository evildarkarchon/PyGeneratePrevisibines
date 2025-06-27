"""Tests for configuration management."""

from unittest.mock import patch

import pytest

from PrevisLib.config.registry import find_tool_paths
from PrevisLib.models.data_classes import CKPEConfig


class TestRegistryReader:
    """Test Windows registry reading functionality."""

    @patch("PrevisLib.config.registry.sys.platform", "linux")
    def test_linux_compatibility(self):
        """Test that registry reader works on Linux (returns empty ToolPaths)."""
        tool_paths = find_tool_paths()

        assert tool_paths.creation_kit is None
        assert tool_paths.xedit is None
        assert tool_paths.fallout4 is None
        assert tool_paths.archive2 is None

    def test_find_tool_paths_basic(self):
        """Test basic tool path finding functionality."""
        tool_paths = find_tool_paths()

        # Should return a ToolPaths object
        assert tool_paths is not None
        # On Linux, all paths should be None
        assert tool_paths.creation_kit is None
        assert tool_paths.xedit is None
        assert tool_paths.fallout4 is None


class TestCKPEConfig:
    """Test CKPE configuration data class."""

    def test_toml_config_reading(self, tmp_path):
        """Test reading TOML configuration."""
        config_content = """
[CreationKitPlatformExtended]
bBSPointerHandleExtremly = false
sOutputFile = "test.log"
"""
        config_file = tmp_path / "ckpe.toml"
        config_file.write_text(config_content)

        config = CKPEConfig.from_toml(config_file)

        assert config.handle_setting is False
        assert config.log_output_file == "test.log"
        assert config.config_path == config_file

    def test_ini_config_reading(self, tmp_path):
        """Test reading INI configuration."""
        config_content = """[CreationKitPlatformExtended]
bBSPointerHandleExtremly = true
sOutputFile = custom.log
"""
        config_file = tmp_path / "ckpe.ini"
        config_file.write_text(config_content)

        config = CKPEConfig.from_ini(config_file)

        assert config.handle_setting is True
        assert config.log_output_file == "custom.log"
        assert config.config_path == config_file

    def test_missing_config_file(self, tmp_path):
        """Test handling of missing configuration file."""
        missing_file = tmp_path / "missing.toml"

        with pytest.raises(FileNotFoundError):
            CKPEConfig.from_toml(missing_file)

    def test_malformed_toml(self, tmp_path):
        """Test handling of malformed TOML."""
        config_content = """[CreationKitPlatformExtended
missing closing bracket
"""
        config_file = tmp_path / "malformed.toml"
        config_file.write_text(config_content)

        with pytest.raises(Exception):  # Should raise parsing error
            CKPEConfig.from_toml(config_file)

    def test_default_values(self, tmp_path):
        """Test default values when sections are missing."""
        config_content = """[SomeOtherSection]
key = "value"
"""
        config_file = tmp_path / "minimal.toml"
        config_file.write_text(config_content)

        config = CKPEConfig.from_toml(config_file)

        # Should use defaults when CKPE section is missing
        assert config.handle_setting is True  # Default value
        assert config.log_output_file == ""  # Default value
