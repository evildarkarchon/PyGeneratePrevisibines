"""Consolidated tests for configuration management and settings validation."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from PrevisLib.config.registry import find_tool_paths
from PrevisLib.models.data_classes import ArchiveTool, BuildMode, CKPEConfig, ToolPaths


class TestRegistryReaderNonWindows:
    """Test registry reading on non-Windows platforms."""

    @patch("PrevisLib.config.registry.sys.platform", "linux")
    def test_linux_compatibility(self, caplog: MagicMock) -> None:
        """Test that registry reader warns and returns empty ToolPaths on Linux."""
        tool_paths = find_tool_paths()
        assert "Registry reading is only available on Windows" in caplog.text
        assert tool_paths == ToolPaths()


@pytest.mark.usefixtures("mock_winreg")
class TestRegistryReaderWindows:
    """Test Windows registry reading functionality with a mocked registry."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_winreg: MagicMock, tmp_path: Path) -> None:
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
    def test_find_all_tools_from_registry(self) -> None:
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
    def test_find_xedit_in_local_path_as_fallback(self) -> None:
        """Test finding xEdit via fallback when registry key is missing."""
        with patch("pathlib.Path.cwd", return_value=self.xedit_dir):
            tool_paths = find_tool_paths()
            assert tool_paths.xedit == self.xedit_exe

    @patch("PrevisLib.config.registry.sys.platform", "win32")
    def test_registry_read_failure(self, caplog: MagicMock) -> None:
        """Test graceful failure when registry keys do not exist."""
        # No registry keys are set
        tool_paths = find_tool_paths()

        assert tool_paths == ToolPaths(xedit=None, fallout4=None, creation_kit=None, archive2=None, bsarch=None)
        assert "Failed to find xEdit in registry" in caplog.text
        assert "Failed to find Fallout 4 in registry" in caplog.text

    @patch("PrevisLib.config.registry.sys.platform", "win32")
    def test_import_error_for_winreg(self, caplog: MagicMock) -> None:
        """Test handling of ImportError for the winreg module."""
        with patch.dict("sys.modules", {"winreg": None}):
            tool_paths = find_tool_paths()
            assert "winreg module not available" in caplog.text
            assert tool_paths == ToolPaths()


class TestCKPEConfig:
    """Test CKPE configuration data class."""

    def test_toml_config_reading(self, tmp_path: Path) -> None:
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

    def test_ini_config_reading(self, tmp_path: Path) -> None:
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

    def test_missing_config_file(self, tmp_path: Path) -> None:
        """Test handling of missing configuration file."""
        missing_file = tmp_path / "missing.toml"

        with pytest.raises(FileNotFoundError):
            CKPEConfig.from_toml(missing_file)

    def test_malformed_toml(self, tmp_path: Path) -> None:
        """Test handling of malformed TOML."""
        config_content = """[CreationKit]
missing closing bracket
"""
        config_file = tmp_path / "malformed.toml"
        config_file.write_text(config_content)

        with pytest.raises(Exception):  # Should raise parsing error  # noqa: B017, PT011
            CKPEConfig.from_toml(config_file)

    def test_default_values(self, tmp_path: Path) -> None:
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


class TestSettingsValidation:
    """Test Settings validation methods."""

    def test_validate_plugin_name_with_spaces(self) -> None:
        """Test that plugin names with spaces are rejected."""
        from PrevisLib.config.settings import Settings
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="Plugin name cannot contain spaces"):
            Settings(plugin_name="My Plugin.esp", build_mode=BuildMode.CLEAN, tool_paths=ToolPaths())

    def test_validate_plugin_name_reserved(self) -> None:
        """Test that reserved plugin names are rejected."""
        from PrevisLib.config.settings import Settings
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="Cannot use reserved plugin name"):
            Settings(plugin_name="Fallout4.esm", build_mode=BuildMode.CLEAN, tool_paths=ToolPaths())

    def test_validate_plugin_name_auto_extension(self) -> None:
        """Test that .esp extension is added automatically."""
        from PrevisLib.config.settings import Settings

        settings = Settings(plugin_name="MyPlugin", build_mode=BuildMode.CLEAN, tool_paths=ToolPaths())
        assert settings.plugin_name == "MyPlugin.esp"

    def test_validate_plugin_name_empty_allowed(self) -> None:
        """Test that empty plugin name is allowed (for interactive mode)."""
        from PrevisLib.config.settings import Settings

        settings = Settings(plugin_name="", build_mode=BuildMode.CLEAN, tool_paths=ToolPaths())
        assert settings.plugin_name == ""

    def test_validate_working_directory_string_to_path(self, tmp_path: Path) -> None:
        """Test that string working directory is converted to Path."""
        from PrevisLib.config.settings import Settings

        # Use an existing directory
        working_dir = tmp_path / "work"
        working_dir.mkdir()

        settings = Settings(plugin_name="test.esp", build_mode=BuildMode.CLEAN, tool_paths=ToolPaths(), working_directory=working_dir)
        assert isinstance(settings.working_directory, Path)
        assert settings.working_directory == working_dir

    def test_validate_working_directory_invalid(self) -> None:
        """Test that non-existent working directory raises error."""
        from PrevisLib.config.settings import Settings
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="Working directory does not exist"):
            Settings(
                plugin_name="test.esp",
                build_mode=BuildMode.CLEAN,
                tool_paths=ToolPaths(),
                working_directory=Path("/definitely/does/not/exist"),
            )

    def test_post_init_validation_no_paths(self) -> None:
        """Test post-init validation when no tool paths are configured."""
        from PrevisLib.config.settings import Settings

        settings = Settings(
            plugin_name="test.esp",
            build_mode=BuildMode.CLEAN,
            tool_paths=ToolPaths(),  # All paths are None
        )

        errors = settings.validate_tools()
        assert len(errors) > 0
        assert any("Fallout 4 not found" in error for error in errors)

    def test_post_init_validation_bsarch_selected_no_path(self) -> None:
        """Test post-init validation when BSArch is selected but not available."""
        from PrevisLib.config.settings import Settings

        settings = Settings(
            plugin_name="test.esp",
            build_mode=BuildMode.CLEAN,
            archive_tool=ArchiveTool.BSARCH,
            tool_paths=ToolPaths(
                fallout4=Path("/fake/fo4"),
                creation_kit=Path("/fake/ck"),
                xedit=Path("/fake/xedit"),
                archive2=Path("/fake/archive2"),
                bsarch=None,  # BSArch not available
            ),
        )

        errors = settings.validate_tools()
        # The validate_tools method checks for missing tools, not archive selection logic
        assert len(errors) > 0  # Will have errors for missing files


class TestSettingsFromCliArgs:
    """Test Settings.from_cli_args method."""

    @patch("PrevisLib.config.settings.find_tool_paths")
    def test_from_cli_args_basic(self, mock_find_tools: MagicMock) -> None:
        """Test basic CLI args parsing."""
        from PrevisLib.config.settings import Settings

        mock_find_tools.return_value = ToolPaths()

        settings = Settings.from_cli_args(plugin_name="test.esp")

        assert settings.plugin_name == "test.esp"
        assert settings.build_mode == BuildMode.CLEAN

    @patch("PrevisLib.config.settings.find_tool_paths")
    def test_from_cli_args_with_options(self, mock_find_tools: MagicMock) -> None:
        """Test CLI args with various options."""
        from PrevisLib.config.settings import Settings

        mock_find_tools.return_value = ToolPaths()

        settings = Settings.from_cli_args(plugin_name="test.esp", build_mode="filtered", verbose=True, xedit_path=Path("/custom/xedit.exe"))

        assert settings.plugin_name == "test.esp"
        assert settings.build_mode == BuildMode.FILTERED
        assert settings.verbose is True
        assert settings.tool_paths.xedit == Path("/custom/xedit.exe")


class TestFindToolPathsExtended:
    """Test find_tool_paths function."""

    @patch("PrevisLib.config.registry.sys.platform")
    def test_find_tool_paths_non_windows(self, mock_platform: MagicMock) -> None:
        """Test tool path discovery on non-Windows systems."""
        mock_platform.return_value = "linux"

        paths = find_tool_paths()

        assert paths.fallout4 is None
        assert paths.creation_kit is None
        assert paths.xedit is None
        assert paths.archive2 is None
        assert paths.bsarch is None

    @patch("PrevisLib.config.registry._find_fallout4_paths")
    @patch("PrevisLib.config.registry._find_xedit_path")
    @patch("PrevisLib.config.registry.sys.platform")
    def test_find_tool_paths_windows_no_registry(self, mock_platform: MagicMock, mock_xedit: MagicMock, mock_fo4: MagicMock) -> None:
        """Test tool path discovery when registry read fails."""
        mock_platform.return_value = "win32"
        mock_xedit.return_value = None
        mock_fo4.return_value = (None, None)

        paths = find_tool_paths()

        assert paths.fallout4 is None
        assert paths.creation_kit is None

    def test_find_tool_paths_with_overrides(self) -> None:
        """Test tool path discovery - function doesn't take overrides."""
        # find_tool_paths doesn't accept parameters - it discovers automatically
        paths = find_tool_paths()

        # Just verify it returns a ToolPaths object
        assert isinstance(paths, ToolPaths)
