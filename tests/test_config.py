"""Tests for configuration management."""

from unittest.mock import patch

import pytest

from PrevisLib.config.registry import find_tool_paths
from PrevisLib.models.data_classes import CKPEConfig, ToolPaths


class TestRegistryReaderNonWindows:
    """Test registry reading on non-Windows platforms."""

    @patch("PrevisLib.config.registry.sys.platform", "linux")
    def test_linux_compatibility(self, caplog):
        """Test that registry reader warns and returns empty ToolPaths on Linux."""
        tool_paths = find_tool_paths()
        assert "Registry reading is only available on Windows" in caplog.text
        assert tool_paths == ToolPaths()


@pytest.mark.usefixtures("mock_winreg")
class TestRegistryReaderWindows:
    """Test Windows registry reading functionality with a mocked registry."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_winreg, tmp_path):
        """Setup for each test."""
        self.mock_winreg = mock_winreg
        self.tmp_path = tmp_path
        self.mock_winreg.Clear()

        # Common paths
        self.fallout4_dir = self.tmp_path / "Fallout 4"
        self.fallout4_dir.mkdir()
        self.fo4_exe = self.fallout4_dir / "Fallout4.exe"
        self.fo4_exe.touch()
        self.ck_exe = self.fallout4_dir / "CreationKit.exe"
        self.ck_exe.touch()

        self.xedit_dir = self.tmp_path / "xEdit"
        self.xedit_dir.mkdir()
        self.xedit_exe = self.xedit_dir / "xEdit.exe"
        self.xedit_exe.touch()

    @patch("PrevisLib.config.registry.sys.platform", "win32")
    def test_find_all_tools_from_registry(self):
        """Test finding all tools via registry keys."""
        # Set up registry
        self.mock_winreg.SetValue(
            self.mock_winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Wow6432Node\Bethesda Softworks\Fallout4",
            "installed path",
            str(self.fallout4_dir),
        )
        self.mock_winreg.SetValue(self.mock_winreg.HKEY_CLASSES_ROOT, r"FO4Script\DefaultIcon", "", str(self.xedit_exe))

        # Set up additional tools that depend on game/xedit paths
        (self.fallout4_dir / "Tools" / "Archive2").mkdir(parents=True)
        archive2_exe = self.fallout4_dir / "Tools" / "Archive2" / "Archive2.exe"
        archive2_exe.touch()
        bsarch_exe = self.xedit_dir / "BSArch.exe"
        bsarch_exe.touch()

        tool_paths = find_tool_paths()

        assert tool_paths.fallout4 == self.fo4_exe
        assert tool_paths.creation_kit == self.ck_exe
        assert tool_paths.xedit == self.xedit_exe
        assert tool_paths.archive2 == archive2_exe
        assert tool_paths.bsarch == bsarch_exe

    @patch("PrevisLib.config.registry.sys.platform", "win32")
    def test_find_xedit_in_local_path_as_fallback(self):
        """Test finding xEdit via fallback when registry key is missing."""
        with patch("pathlib.Path.cwd", return_value=self.xedit_dir):
            tool_paths = find_tool_paths()
            assert tool_paths.xedit == self.xedit_exe

    @patch("PrevisLib.config.registry.sys.platform", "win32")
    def test_registry_read_failure(self, caplog):
        """Test graceful failure when registry keys do not exist."""
        # No registry keys are set
        tool_paths = find_tool_paths()

        assert tool_paths == ToolPaths(xedit=None, fallout4=None, creation_kit=None, archive2=None, bsarch=None)
        assert "Failed to find xEdit in registry" in caplog.text
        assert "Failed to find Fallout 4 in registry" in caplog.text

    @patch("PrevisLib.config.registry.sys.platform", "win32")
    def test_import_error_for_winreg(self, caplog):
        """Test handling of ImportError for the winreg module."""
        with patch.dict("sys.modules", {"winreg": None}):
            tool_paths = find_tool_paths()
            assert "winreg module not available" in caplog.text
            assert tool_paths == ToolPaths()


class TestCKPEConfig:
    """Test CKPE configuration data class."""

    def test_toml_config_reading(self, tmp_path):
        """Test reading TOML configuration."""
        config_content = """
[CreationKit]
bBSPointerHandleExtremly = false

[Log]
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
        config_content = """[CreationKit]
bBSPointerHandleExtremly = true

[Log]
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
        config_content = """[CreationKit]
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
        assert config.handle_setting is False  # Default value from implementation
        assert config.log_output_file == ""  # Default value
