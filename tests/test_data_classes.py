"""Tests for data classes and models."""

from pathlib import Path

from PrevisLib.models.data_classes import ArchiveTool, BuildMode, BuildStep, CKPEConfig, ToolPaths


class TestEnums:
    """Test enumeration classes."""

    def test_build_mode_values(self) -> None:
        """Test BuildMode enum values."""
        assert BuildMode.CLEAN.value == "clean"
        assert BuildMode.FILTERED.value == "filtered"
        assert BuildMode.XBOX.value == "xbox"

    def test_build_step_string_representation(self) -> None:
        """Test BuildStep string formatting."""
        assert str(BuildStep.GENERATE_PRECOMBINED) == "Generate Precombined"
        assert str(BuildStep.MERGE_COMBINED_OBJECTS) == "Merge Combined Objects"
        assert str(BuildStep.FINAL_PACKAGING) == "Final Packaging"

    def test_archive_tool_values(self) -> None:
        """Test ArchiveTool enum values."""
        assert ArchiveTool.ARCHIVE2.value == "Archive2"
        assert ArchiveTool.BSARCH.value == "BSArch"


class TestToolPaths:
    """Test ToolPaths data class."""

    def test_default_initialization(self) -> None:
        """Test default ToolPaths initialization."""
        paths = ToolPaths()
        assert paths.creation_kit is None
        assert paths.xedit is None
        assert paths.archive2 is None
        assert paths.bsarch is None
        assert paths.fallout4 is None

    def test_validation_with_no_tools(self) -> None:
        """Test validation when no tools are configured."""
        paths = ToolPaths()
        errors = paths.validate()

        expected_errors = [
            "Creation Kit not found",
            "xEdit/FO4Edit not found",
            "Fallout 4 not found",
            "No archive tool found (Archive2 or BSArch)",
        ]

        assert all(error in errors for error in expected_errors)

    def test_validation_with_nonexistent_tools(self) -> None:
        """Test validation with non-existent tool paths."""
        paths = ToolPaths(
            creation_kit=Path("/fake/ck.exe"),
            xedit=Path("/fake/xedit.exe"),
            fallout4=Path("/fake/fo4.exe"),
            archive2=Path("/fake/archive2.exe"),
        )

        errors = paths.validate()
        assert len(errors) >= 3  # At least CK, xEdit, and FO4 not found

    def test_validation_with_valid_tools_but_missing_scripts(self, tmp_path: Path) -> None:
        """Test validation with valid tools but missing xEdit scripts."""
        # Create fake tool files
        ck_path = tmp_path / "CreationKit.exe"
        xedit_path = tmp_path / "FO4Edit.exe"
        fo4_path = tmp_path / "Fallout4.exe"
        archive_path = tmp_path / "Archive2.exe"

        for path in [ck_path, xedit_path, fo4_path, archive_path]:
            path.write_text("fake executable")

        paths = ToolPaths(creation_kit=ck_path, xedit=xedit_path, fallout4=fo4_path, archive2=archive_path)

        errors = paths.validate()

        # Should have script validation error since Edit Scripts directory doesn't exist
        assert any("xEdit scripts validation failed" in error for error in errors)
        assert any("Edit Scripts directory not found" in error for error in errors)

    def test_validation_with_valid_tools_and_scripts(self, tmp_path: Path) -> None:
        """Test validation with valid tools and xEdit scripts."""
        # Create fake tool files
        ck_path = tmp_path / "CreationKit.exe"
        xedit_path = tmp_path / "FO4Edit.exe"
        fo4_path = tmp_path / "Fallout4.exe"
        archive_path = tmp_path / "Archive2.exe"

        for path in [ck_path, xedit_path, fo4_path, archive_path]:
            path.write_text("fake executable")

        # Create Edit Scripts directory with required scripts
        scripts_dir = tmp_path / "Edit Scripts"
        scripts_dir.mkdir()

        # Create required scripts with correct versions
        script1 = scripts_dir / "Batch_FO4MergePrevisandCleanRefr.pas"
        script1.write_text("// Script with V2.2 version")

        script2 = scripts_dir / "Batch_FO4MergeCombinedObjectsAndCheck.pas"
        script2.write_text("// Script with V1.5 version")

        paths = ToolPaths(creation_kit=ck_path, xedit=xedit_path, fallout4=fo4_path, archive2=archive_path)

        errors = paths.validate()
        assert len(errors) == 0


class TestCKPEConfig:
    """Test CKPE configuration data class."""

    def test_default_initialization(self, tmp_path: Path) -> None:
        """Test default CKPE config initialization."""
        # Create a minimal TOML config file
        config_file = tmp_path / "test.toml"
        config_file.write_text("""
[CreationKit]
bBSPointerHandleExtremly = true

[Log]
sOutputFile = ""
""")

        config = CKPEConfig.from_toml(config_file)

        assert config.handle_setting is True
        assert config.log_output_file == ""
        assert config.config_path == config_file
        assert isinstance(config.raw_config, dict)

    def test_custom_initialization(self, tmp_path: Path) -> None:
        """Test CKPE config with custom values."""
        # Create a TOML config file with custom settings
        config_file = tmp_path / "custom.toml"
        config_file.write_text("""
[CreationKit]
bBSPointerHandleExtremly = false

[Log]
sOutputFile = "test.log"
""")

        config = CKPEConfig.from_toml(config_file)

        assert config.handle_setting is False
        assert config.log_output_file == "test.log"
        assert config.config_path == config_file
        assert isinstance(config.raw_config, dict)

    def test_direct_instantiation_prevented(self) -> None:
        """Test that direct instantiation of CKPEConfig is prevented."""
        import pytest

        with pytest.raises(TypeError, match="CKPEConfig cannot be instantiated directly"):
            CKPEConfig()

        with pytest.raises(TypeError, match="CKPEConfig cannot be instantiated directly"):
            CKPEConfig(handle_setting=True, log_output_file="test.log")
