"""Tests for data classes and models."""

import pytest
from pathlib import Path

from PrevisLib.models.data_classes import (
    BuildMode, BuildStep, ArchiveTool, ToolPaths, CKPEConfig
)


class TestEnums:
    """Test enumeration classes."""
    
    def test_build_mode_values(self):
        """Test BuildMode enum values."""
        assert BuildMode.CLEAN.value == "clean"
        assert BuildMode.FILTERED.value == "filtered"
        assert BuildMode.XBOX.value == "xbox"
        
    def test_build_step_string_representation(self):
        """Test BuildStep string formatting."""
        assert str(BuildStep.GENERATE_PRECOMBINED) == "Generate Precombined"
        assert str(BuildStep.MERGE_COMBINED_OBJECTS) == "Merge Combined Objects"
        assert str(BuildStep.FINAL_PACKAGING) == "Final Packaging"
        
    def test_archive_tool_values(self):
        """Test ArchiveTool enum values."""
        assert ArchiveTool.ARCHIVE2.value == "Archive2"
        assert ArchiveTool.BSARCH.value == "BSArch"


class TestToolPaths:
    """Test ToolPaths data class."""
    
    def test_default_initialization(self):
        """Test default ToolPaths initialization."""
        paths = ToolPaths()
        assert paths.creation_kit is None
        assert paths.xedit is None
        assert paths.archive2 is None
        assert paths.bsarch is None
        assert paths.fallout4 is None
        
    def test_validation_with_no_tools(self):
        """Test validation when no tools are configured."""
        paths = ToolPaths()
        errors = paths.validate()
        
        expected_errors = [
            "Creation Kit not found",
            "xEdit/FO4Edit not found", 
            "Fallout 4 not found",
            "No archive tool found (Archive2 or BSArch)"
        ]
        
        assert all(error in errors for error in expected_errors)
        
    def test_validation_with_nonexistent_tools(self):
        """Test validation with non-existent tool paths."""
        paths = ToolPaths(
            creation_kit=Path("/fake/ck.exe"),
            xedit=Path("/fake/xedit.exe"),
            fallout4=Path("/fake/fo4.exe"),
            archive2=Path("/fake/archive2.exe")
        )
        
        errors = paths.validate()
        assert len(errors) >= 3  # At least CK, xEdit, and FO4 not found
        
    def test_validation_with_valid_tools(self, tmp_path):
        """Test validation with valid tool paths."""
        # Create fake tool files
        ck_path = tmp_path / "CreationKit.exe"
        xedit_path = tmp_path / "FO4Edit.exe"
        fo4_path = tmp_path / "Fallout4.exe"
        archive_path = tmp_path / "Archive2.exe"
        
        for path in [ck_path, xedit_path, fo4_path, archive_path]:
            path.write_text("fake executable")
            
        paths = ToolPaths(
            creation_kit=ck_path,
            xedit=xedit_path,
            fallout4=fo4_path,
            archive2=archive_path
        )
        
        errors = paths.validate()
        assert len(errors) == 0


class TestCKPEConfig:
    """Test CKPE configuration data class."""
    
    def test_default_initialization(self):
        """Test default CKPE config initialization."""
        config = CKPEConfig()
        
        assert config.handle_setting is True
        assert config.log_output_file == ""
        assert config.config_path is None
        assert config.raw_config == {}
        
    def test_custom_initialization(self):
        """Test CKPE config with custom values."""
        config = CKPEConfig(
            handle_setting=False,
            log_output_file="test.log",
            config_path=Path("test.toml"),
            raw_config={"test": "value"}
        )
        
        assert config.handle_setting is False
        assert config.log_output_file == "test.log"
        assert config.config_path == Path("test.toml")
        assert config.raw_config == {"test": "value"}