"""Tests for validation utilities."""

from pathlib import Path

from PrevisLib.utils.validation import (
    RESERVED_PLUGIN_NAMES,
    VALID_PLUGIN_EXTENSIONS,
    check_tool_version,
    validate_archive_format,
    validate_ckpe_config,
    validate_directory,
    validate_plugin_name,
    validate_tool_path,
)


class TestPluginValidation:
    """Test plugin name validation."""

    def test_valid_plugin_names(self):
        """Test that valid plugin names are accepted."""
        valid_names = ["MyMod.esp", "TestPlugin.esm", "Patch.esl", "Very_Long_Plugin_Name.esp", "mod-with-hyphens.esp", "123numbers.esp"]

        for name in valid_names:
            is_valid, message = validate_plugin_name(name)
            assert is_valid, f"Expected {name} to be valid, got: {message}"

    def test_invalid_plugin_extensions(self):
        """Test that invalid extensions are rejected."""
        invalid_names = ["plugin.txt", "mod.ini", "test.exe", "plugin.bat", "no_extension"]

        for name in invalid_names:
            is_valid, message = validate_plugin_name(name)
            assert not is_valid
            assert "extension" in message.lower()

    def test_reserved_plugin_names(self):
        """Test that reserved plugin names are rejected."""
        # Test all reserved names from the constant
        for name in RESERVED_PLUGIN_NAMES:
            is_valid, message = validate_plugin_name(name)
            assert not is_valid
            assert "reserved" in message.lower()

    def test_plugin_name_with_spaces(self):
        """Test that plugin names with spaces are rejected."""
        is_valid, message = validate_plugin_name("My Plugin.esp")
        assert not is_valid
        assert "spaces" in message.lower()

    def test_empty_plugin_name(self):
        """Test that empty plugin names are rejected."""
        is_valid, message = validate_plugin_name("")
        assert not is_valid
        assert "empty" in message.lower()

    def test_case_insensitive_extension(self):
        """Test that extensions are case insensitive."""
        test_cases = ["TestMod.ESP", "TestMod.ESM", "TestMod.ESL", "TestMod.esp", "TestMod.esm", "TestMod.esl"]

        for name in test_cases:
            is_valid, message = validate_plugin_name(name)
            assert is_valid, f"Expected case insensitive extension to work: {name}, {message}"

    def test_valid_extensions_constant(self):
        """Test that all valid extensions are properly defined."""
        assert ".esp" in VALID_PLUGIN_EXTENSIONS
        assert ".esm" in VALID_PLUGIN_EXTENSIONS
        assert ".esl" in VALID_PLUGIN_EXTENSIONS
        assert len(VALID_PLUGIN_EXTENSIONS) == 3


class TestToolValidation:
    """Test tool path validation."""

    def test_none_path(self):
        """Test validation with None path."""
        is_valid, message = validate_tool_path(None, "TestTool")
        assert not is_valid
        assert "not specified" in message

    def test_nonexistent_path(self):
        """Test validation of non-existent path."""
        is_valid, message = validate_tool_path(Path("/nonexistent/tool.exe"), "TestTool")
        assert not is_valid
        assert "not found" in message

    def test_directory_instead_of_file(self, tmp_path):
        """Test validation when path points to directory."""
        directory = tmp_path / "tool_dir"
        directory.mkdir()

        is_valid, message = validate_tool_path(directory, "TestTool")
        assert not is_valid
        assert "not a file" in message

    def test_non_executable_file(self, tmp_path):
        """Test validation of non-.exe file."""
        txt_file = tmp_path / "tool.txt"
        txt_file.write_text("not executable")

        is_valid, message = validate_tool_path(txt_file, "TestTool")
        assert not is_valid
        assert "executable" in message

    def test_valid_executable(self, tmp_path):
        """Test validation of valid executable."""
        exe_file = tmp_path / "tool.exe"
        exe_file.write_text("fake executable")

        is_valid, message = validate_tool_path(exe_file, "TestTool")
        assert is_valid
        assert "found and validated" in message


class TestDirectoryValidation:
    """Test directory validation."""

    def test_existing_directory(self, tmp_path):
        """Test validation of existing directory."""
        test_dir = tmp_path / "existing"
        test_dir.mkdir()

        is_valid, message = validate_directory(test_dir, "TestDir")
        assert is_valid
        assert message == ""

    def test_nonexistent_directory_must_exist(self, tmp_path):
        """Test validation of non-existent directory when must_exist=True."""
        nonexistent = tmp_path / "nonexistent"

        is_valid, message = validate_directory(nonexistent, "TestDir", must_exist=True)
        assert not is_valid
        assert "does not exist" in message

    def test_nonexistent_directory_optional(self, tmp_path):
        """Test validation of non-existent directory when must_exist=False."""
        nonexistent = tmp_path / "nonexistent"

        is_valid, message = validate_directory(nonexistent, "TestDir", must_exist=False)
        assert is_valid
        assert message == ""

    def test_file_instead_of_directory(self, tmp_path):
        """Test validation when path points to file instead of directory."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("content")

        is_valid, message = validate_directory(file_path, "TestDir")
        assert not is_valid
        assert "not a directory" in message


class TestToolVersionCheck:
    """Test tool version checking."""

    def test_nonexistent_tool(self, tmp_path):
        """Test version check for non-existent tool."""
        nonexistent = tmp_path / "nonexistent.exe"

        is_valid, message = check_tool_version(nonexistent)
        assert not is_valid
        assert "not found" in message

    def test_existing_tool(self, tmp_path):
        """Test version check for existing tool."""
        tool_path = tmp_path / "tool.exe"
        tool_path.write_text("fake tool")

        is_valid, message = check_tool_version(tool_path)
        assert is_valid
        assert "not implemented" in message

    def test_version_check_with_expected_version(self, tmp_path):
        """Test version check with expected version parameter."""
        tool_path = tmp_path / "tool.exe"
        tool_path.write_text("fake tool")

        is_valid, message = check_tool_version(tool_path, "1.0.0")
        assert is_valid
        assert "not implemented" in message


class TestCKPEConfigValidation:
    """Test CKPE config validation."""

    def test_nonexistent_config(self, tmp_path):
        """Test validation of non-existent config file."""
        nonexistent = tmp_path / "nonexistent.toml"

        is_valid, message = validate_ckpe_config(nonexistent)
        assert not is_valid
        assert "not found" in message

    def test_invalid_extension(self, tmp_path):
        """Test validation of config with invalid extension."""
        invalid_config = tmp_path / "config.txt"
        invalid_config.write_text("content")

        is_valid, message = validate_ckpe_config(invalid_config)
        assert not is_valid
        assert "must be .toml or .ini" in message

    def test_valid_toml_config(self, tmp_path):
        """Test validation of valid TOML config."""
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[section]
key = "value"
""")

        is_valid, message = validate_ckpe_config(config_file)
        assert is_valid
        assert message == ""

    def test_valid_ini_config(self, tmp_path):
        """Test validation of valid INI config."""
        config_file = tmp_path / "config.ini"
        config_file.write_text("""
[section]
key = value
""")

        is_valid, message = validate_ckpe_config(config_file)
        assert is_valid
        assert message == ""

    def test_malformed_toml_config(self, tmp_path):
        """Test validation of malformed TOML config."""
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[section
missing closing bracket
""")

        is_valid, message = validate_ckpe_config(config_file)
        assert not is_valid
        assert "Failed to parse" in message

    def test_malformed_ini_config(self, tmp_path):
        """Test validation of malformed INI config."""
        config_file = tmp_path / "config.ini"
        config_file.write_text("""
invalid ini content
no sections
""")

        is_valid, message = validate_ckpe_config(config_file)
        assert not is_valid
        assert "Failed to parse" in message


class TestArchiveValidation:
    """Test archive format validation."""

    def test_nonexistent_archive(self, tmp_path):
        """Test validation of non-existent archive."""
        nonexistent = tmp_path / "nonexistent.ba2"

        is_valid, message = validate_archive_format(nonexistent)
        assert not is_valid
        assert "not found" in message

    def test_invalid_archive_extension(self, tmp_path):
        """Test validation of archive with wrong extension."""
        archive_file = tmp_path / "archive.zip"
        archive_file.write_text("fake archive")

        is_valid, message = validate_archive_format(archive_file)
        assert not is_valid
        assert "must be .ba2" in message

    def test_valid_archive(self, tmp_path):
        """Test validation of valid BA2 archive."""
        archive_file = tmp_path / "archive.ba2"
        archive_file.write_text("fake ba2 archive")

        is_valid, message = validate_archive_format(archive_file)
        assert is_valid
        assert message == ""

    def test_case_insensitive_ba2_extension(self, tmp_path):
        """Test that BA2 extension validation is case insensitive."""
        archive_file = tmp_path / "archive.BA2"
        archive_file.write_text("fake ba2 archive")

        is_valid, message = validate_archive_format(archive_file)
        assert is_valid
        assert message == ""
