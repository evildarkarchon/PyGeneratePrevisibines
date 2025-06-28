"""Tests for validation utilities."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from PrevisLib.utils.validation import (
    REQUIRED_XEDIT_SCRIPTS,
    RESERVED_PLUGIN_NAMES,
    VALID_PLUGIN_EXTENSIONS,
    check_tool_version,
    create_plugin_from_template,
    validate_archive_format,
    validate_ckpe_config,
    validate_directory,
    validate_plugin_name,
    validate_tool_path,
    validate_xedit_scripts,
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
        assert "Not a Windows executable - version check skipped" in message

    def test_version_check_with_expected_version(self, tmp_path):
        """Test version check with expected version parameter."""
        tool_path = tmp_path / "tool.exe"
        tool_path.write_text("fake tool")

        is_valid, message = check_tool_version(tool_path, "1.0.0")
        assert is_valid
        assert "Not a Windows executable - version check skipped" in message


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


class TestPluginTemplateCreation:
    """Test plugin template creation functionality."""

    def test_create_plugin_from_template_success(self, tmp_path):
        """Test successful plugin creation from template."""
        data_path = tmp_path / "Data"
        data_path.mkdir()

        # Create template file
        template_path = data_path / "xPrevisPatch.esp"
        template_path.write_text("Template plugin content")

        target_plugin = "MyNewMod.esp"

        with (
            patch("PrevisLib.utils.file_system.mo2_aware_copy") as mock_copy,
            patch("PrevisLib.utils.file_system.wait_for_output_file", return_value=True) as mock_wait,
        ):
            success, message = create_plugin_from_template(data_path, target_plugin)

            assert success is True
            assert "Created MyNewMod.esp from xPrevisPatch.esp template" in message
            mock_copy.assert_called_once()
            mock_wait.assert_called_once()

    def test_create_plugin_from_template_no_template(self, tmp_path):
        """Test plugin creation when template doesn't exist."""
        data_path = tmp_path / "Data"
        data_path.mkdir()

        target_plugin = "MyNewMod.esp"

        success, message = create_plugin_from_template(data_path, target_plugin)

        assert success is False
        assert "xPrevisPatch.esp template not found" in message

    def test_create_plugin_from_template_target_exists(self, tmp_path):
        """Test plugin creation when target already exists."""
        data_path = tmp_path / "Data"
        data_path.mkdir()

        # Create template and target files
        template_path = data_path / "xPrevisPatch.esp"
        template_path.write_text("Template plugin content")

        target_plugin = "MyNewMod.esp"
        target_path = data_path / target_plugin
        target_path.write_text("Existing plugin")

        success, message = create_plugin_from_template(data_path, target_plugin)

        assert success is False
        assert "Plugin MyNewMod.esp already exists" in message

    def test_create_plugin_from_template_archive_exists(self, tmp_path):
        """Test plugin creation when plugin archive already exists."""
        data_path = tmp_path / "Data"
        data_path.mkdir()

        # Create template file
        template_path = data_path / "xPrevisPatch.esp"
        template_path.write_text("Template plugin content")

        # Create existing archive
        target_plugin = "MyNewMod.esp"
        archive_path = data_path / "MyNewMod - Main.ba2"
        archive_path.write_text("Archive content")

        success, message = create_plugin_from_template(data_path, target_plugin)

        assert success is False
        assert "Plugin already has an archive" in message

    def test_create_plugin_from_template_copy_fail(self, tmp_path):
        """Test plugin creation when file copy fails."""
        data_path = tmp_path / "Data"
        data_path.mkdir()

        # Create template file
        template_path = data_path / "xPrevisPatch.esp"
        template_path.write_text("Template plugin content")

        target_plugin = "MyNewMod.esp"

        with patch("PrevisLib.utils.file_system.mo2_aware_copy", side_effect=PermissionError("Access denied")):
            success, message = create_plugin_from_template(data_path, target_plugin)

            assert success is False
            assert "Failed to copy template" in message
            assert "Access denied" in message

    def test_create_plugin_from_template_wait_timeout(self, tmp_path):
        """Test plugin creation when waiting for file times out."""
        data_path = tmp_path / "Data"
        data_path.mkdir()

        # Create template file
        template_path = data_path / "xPrevisPatch.esp"
        template_path.write_text("Template plugin content")

        target_plugin = "MyNewMod.esp"

        with (
            patch("PrevisLib.utils.file_system.mo2_aware_copy") as mock_copy,
            patch("PrevisLib.utils.file_system.wait_for_output_file", return_value=False) as mock_wait,
        ):
            success, message = create_plugin_from_template(data_path, target_plugin)

            assert success is False
            assert "file not accessible after copy" in message
            mock_copy.assert_called_once()
            mock_wait.assert_called_once()

    def test_create_plugin_from_template_different_extensions(self, tmp_path):
        """Test plugin creation with different plugin extensions."""
        data_path = tmp_path / "Data"
        data_path.mkdir()

        # Create template file
        template_path = data_path / "xPrevisPatch.esp"
        template_path.write_text("Template plugin content")

        test_cases = ["MyMod.esp", "MyMod.esm", "MyMod.esl"]

        for target_plugin in test_cases:
            with (
                patch("PrevisLib.utils.file_system.mo2_aware_copy") as mock_copy,
                patch("PrevisLib.utils.file_system.wait_for_output_file", return_value=True),
            ):
                success, message = create_plugin_from_template(data_path, target_plugin)

                assert success is True
                assert f"Created {target_plugin} from xPrevisPatch.esp template" in message
                mock_copy.assert_called_once()

    def test_create_plugin_from_template_auto_append_esp(self, tmp_path):
        """Test that .esp extension is automatically appended when no extension provided."""
        data_path = tmp_path / "Data"
        data_path.mkdir()

        # Create template file
        template_path = data_path / "xPrevisPatch.esp"
        template_path.write_text("Template plugin content")

        target_plugin = "MyNewMod"  # No extension

        with (
            patch("PrevisLib.utils.file_system.mo2_aware_copy") as mock_copy,
            patch("PrevisLib.utils.file_system.wait_for_output_file", return_value=True),
        ):
            success, message = create_plugin_from_template(data_path, target_plugin)

            assert success is True
            assert "Created MyNewMod.esp from xPrevisPatch.esp template" in message
            # Verify that mo2_aware_copy was called with the .esp appended version
            expected_target_path = data_path / "MyNewMod.esp"
            mock_copy.assert_called_once_with(template_path, expected_target_path, delay=2.0)

    def test_create_plugin_from_template_no_extension_conflict_check(self, tmp_path):
        """Test that auto-appended .esp extension is checked for conflicts properly."""
        data_path = tmp_path / "Data"
        data_path.mkdir()

        # Create template file
        template_path = data_path / "xPrevisPatch.esp"
        template_path.write_text("Template plugin content")

        # Create existing plugin with .esp extension
        existing_plugin = data_path / "MyNewMod.esp"
        existing_plugin.write_text("Existing plugin")

        target_plugin = "MyNewMod"  # No extension, but MyNewMod.esp already exists

        success, message = create_plugin_from_template(data_path, target_plugin)

        assert success is False
        assert "Plugin MyNewMod.esp already exists" in message

    def test_create_plugin_from_template_no_extension_archive_check(self, tmp_path):
        """Test that auto-appended .esp extension is checked for archive conflicts."""
        data_path = tmp_path / "Data"
        data_path.mkdir()

        # Create template file
        template_path = data_path / "xPrevisPatch.esp"
        template_path.write_text("Template plugin content")

        # Create existing archive for what would become MyNewMod.esp
        archive_path = data_path / "MyNewMod - Main.ba2"
        archive_path.write_text("Archive content")

        target_plugin = "MyNewMod"  # No extension

        success, message = create_plugin_from_template(data_path, target_plugin)

        assert success is False
        assert "Plugin already has an archive" in message


class TestXEditScriptValidation:
    """Test xEdit script validation."""

    def test_nonexistent_xedit_path(self):
        """Test validation with non-existent xEdit path."""
        nonexistent_path = Path("/nonexistent/xedit.exe")

        is_valid, message = validate_xedit_scripts(nonexistent_path)
        assert not is_valid
        assert "xEdit path not found" in message

    def test_none_xedit_path(self):
        """Test validation with None xEdit path."""
        is_valid, message = validate_xedit_scripts(None)
        assert not is_valid
        assert "xEdit path not found" in message

    def test_missing_edit_scripts_directory(self, tmp_path):
        """Test validation when Edit Scripts directory doesn't exist."""
        xedit_exe = tmp_path / "xEdit.exe"
        xedit_exe.write_text("fake executable")

        is_valid, message = validate_xedit_scripts(xedit_exe)
        assert not is_valid
        assert "Edit Scripts directory not found" in message

    def test_missing_required_scripts(self, tmp_path):
        """Test validation when required scripts are missing."""
        # Create xEdit structure
        xedit_exe = tmp_path / "xEdit.exe"
        xedit_exe.write_text("fake executable")

        scripts_dir = tmp_path / "Edit Scripts"
        scripts_dir.mkdir()

        is_valid, message = validate_xedit_scripts(xedit_exe)
        assert not is_valid
        assert "Missing scripts" in message
        for script_name in REQUIRED_XEDIT_SCRIPTS.keys():
            assert script_name in message

    def test_scripts_with_wrong_versions(self, tmp_path):
        """Test validation when scripts exist but have wrong versions."""
        # Create xEdit structure
        xedit_exe = tmp_path / "xEdit.exe"
        xedit_exe.write_text("fake executable")

        scripts_dir = tmp_path / "Edit Scripts"
        scripts_dir.mkdir()

        # Create scripts with wrong versions
        for script_name in REQUIRED_XEDIT_SCRIPTS.keys():
            script_path = scripts_dir / script_name
            script_path.write_text("// Old script version V1.0\nsome script content")

        is_valid, message = validate_xedit_scripts(xedit_exe)
        assert not is_valid
        assert "Version mismatches" in message

    def test_scripts_with_correct_versions(self, tmp_path):
        """Test validation when all scripts exist with correct versions."""
        # Create xEdit structure
        xedit_exe = tmp_path / "xEdit.exe"
        xedit_exe.write_text("fake executable")

        scripts_dir = tmp_path / "Edit Scripts"
        scripts_dir.mkdir()

        # Create scripts with correct versions
        for script_name, required_version in REQUIRED_XEDIT_SCRIPTS.items():
            script_path = scripts_dir / script_name
            script_path.write_text(f"// Script {script_name} {required_version}\nsome script content")

        is_valid, message = validate_xedit_scripts(xedit_exe)
        assert is_valid
        assert "All required xEdit scripts found with correct versions" in message

    def test_scripts_case_insensitive_version_check(self, tmp_path):
        """Test that version checking is case-insensitive."""
        # Create xEdit structure
        xedit_exe = tmp_path / "xEdit.exe"
        xedit_exe.write_text("fake executable")

        scripts_dir = tmp_path / "Edit Scripts"
        scripts_dir.mkdir()

        # Create scripts with lowercase versions (should still match uppercase required versions)
        for script_name, required_version in REQUIRED_XEDIT_SCRIPTS.items():
            script_path = scripts_dir / script_name
            script_path.write_text(f"// Script {script_name} {required_version.lower()}\nsome script content")

        is_valid, message = validate_xedit_scripts(xedit_exe)
        assert is_valid
        assert "All required xEdit scripts found with correct versions" in message

    def test_mixed_script_issues(self, tmp_path):
        """Test validation with mixed script issues (missing and wrong version)."""
        # Create xEdit structure
        xedit_exe = tmp_path / "xEdit.exe"
        xedit_exe.write_text("fake executable")

        scripts_dir = tmp_path / "Edit Scripts"
        scripts_dir.mkdir()

        # Create only one script with wrong version, leave the other missing
        script_names = list(REQUIRED_XEDIT_SCRIPTS.keys())
        first_script = scripts_dir / script_names[0]
        first_script.write_text("// Old version V1.0")

        # Don't create the second script (leave it missing)

        is_valid, message = validate_xedit_scripts(xedit_exe)
        assert not is_valid
        assert "Missing scripts" in message and "Version mismatches" in message
