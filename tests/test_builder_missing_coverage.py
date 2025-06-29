"""Tests to improve coverage for remaining uncovered lines in builder.py."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from PrevisLib.config.settings import Settings
from PrevisLib.core.builder import PrevisBuilder
from PrevisLib.models.data_classes import ArchiveTool, BuildMode, BuildStep, ToolPaths


class TestBuilderValidationEdgeCases:
    """Test edge cases in builder validation."""

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    def test_init_no_creation_kit_path(self, mock_validate):
        """Test initialization when Creation Kit path is missing."""
        settings = Settings(
            plugin_name="test.esp",
            build_mode=BuildMode.CLEAN,
            tool_paths=ToolPaths(
                creation_kit=None,  # Missing
                xedit=Path("/fake/xedit"),
                fallout4=Path("/fake/fo4"),
                archive2=Path("/fake/archive2")
            )
        )
        
        with pytest.raises(ValueError, match="Creation Kit path is required but not configured"):
            PrevisBuilder(settings)

    def test_init_no_xedit_path(self):
        """Test initialization when xEdit path is missing."""
        settings = Settings(
            plugin_name="test.esp",
            build_mode=BuildMode.CLEAN,
            tool_paths=ToolPaths(
                creation_kit=Path("/fake/ck"),
                xedit=None,  # Missing
                fallout4=Path("/fake/fo4"),
                archive2=Path("/fake/archive2")
            )
        )
        
        with pytest.raises(ValueError, match="xEdit path is required but not configured"):
            PrevisBuilder(settings)

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    def test_init_no_fallout4_path(self, mock_validate):
        """Test initialization when Fallout 4 path is missing."""
        mock_validate.return_value = (True, "OK")
        
        settings = Settings(
            plugin_name="test.esp",
            build_mode=BuildMode.CLEAN,
            tool_paths=ToolPaths(
                creation_kit=Path("/fake/ck"),
                xedit=Path("/fake/xedit"),
                fallout4=None,  # Missing
                archive2=Path("/fake/archive2")
            )
        )
        
        with pytest.raises(ValueError, match="Fallout 4 path is required but not configured"):
            PrevisBuilder(settings)

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    def test_get_resume_options_with_failed_step(self, mock_validate):
        """Test get_resume_options when there's a failed step."""
        mock_validate.return_value = (True, "OK")
        
        settings = Settings(
            plugin_name="test.esp",
            build_mode=BuildMode.CLEAN,
            tool_paths=ToolPaths(
                creation_kit=Path("/fake/ck"),
                xedit=Path("/fake/xedit"),
                fallout4=Path("/fake/fo4"),
                archive2=Path("/fake/archive2")
            )
        )
        
        builder = PrevisBuilder(settings)
        builder.failed_step = BuildStep.GENERATE_PREVIS
        
        resume_options = builder.get_resume_options()
        
        # Should offer to resume from failed step and all subsequent steps
        assert BuildStep.GENERATE_PREVIS in resume_options
        assert BuildStep.PACKAGE_BA2 in resume_options

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    def test_get_steps_all_modes(self, mock_validate):
        """Test _get_steps for different build modes."""
        mock_validate.return_value = (True, "OK")
        
        # Test CLEAN mode
        settings = Settings(
            plugin_name="test.esp",
            build_mode=BuildMode.CLEAN,
            tool_paths=ToolPaths(
                creation_kit=Path("/fake/ck"),
                xedit=Path("/fake/xedit"),
                fallout4=Path("/fake/fo4"),
                archive2=Path("/fake/archive2")
            )
        )
        
        builder = PrevisBuilder(settings)
        steps = builder._get_steps()
        
        # Clean mode should have all steps
        assert BuildStep.CLEAN_PREVIS in steps
        assert BuildStep.GENERATE_PRECOMBINED in steps
        assert BuildStep.GENERATE_PREVIS in steps
        assert BuildStep.PACK_PREVIS_SCRIPTS in steps
        assert BuildStep.GENERATE_PSG in steps
        assert BuildStep.PACK_GEOMETRY_SCRIPTS in steps
        assert BuildStep.GENERATE_CDX in steps
        assert BuildStep.COMPRESS_PSG in steps
        assert BuildStep.COMPRESS_CDX in steps
        assert BuildStep.PACKAGE_BA2 in steps

    @patch("PrevisLib.core.builder.logger")
    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    def test_build_resume_with_invalid_step(self, mock_validate, mock_logger):
        """Test build with invalid start_from_step."""
        mock_validate.return_value = (True, "OK")
        
        settings = Settings(
            plugin_name="test.esp",
            build_mode=BuildMode.FILTERED,  # Filtered mode
            tool_paths=ToolPaths(
                creation_kit=Path("/fake/ck"),
                xedit=Path("/fake/xedit"),
                fallout4=Path("/fake/fo4"),
                archive2=Path("/fake/archive2")
            )
        )
        
        builder = PrevisBuilder(settings)
        
        # Try to resume from CLEAN_PREVIS which isn't in filtered mode steps
        with patch.object(builder, "_package_files", return_value=True):
            result = builder.build(start_from_step=BuildStep.CLEAN_PREVIS)
        
        assert result is True  # Should succeed but skip the invalid step
        mock_logger.warning.assert_called_with(
            "Requested start step CLEAN_PREVIS not in build sequence, starting from beginning"
        )


class TestPackageFilesEdgeCases:
    """Test additional edge cases in _package_files."""

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    @patch("PrevisLib.core.builder.logger")
    def test_package_files_create_archive_fails(self, mock_logger, mock_validate, tmp_path):
        """Test when archive creation fails."""
        mock_validate.return_value = (True, "OK")
        
        # Setup
        fo4_path = tmp_path / "Fallout4"
        data_path = fo4_path / "Data"
        data_path.mkdir(parents=True)
        
        settings = Settings(
            plugin_name="test.esp",
            build_mode=BuildMode.CLEAN,
            tool_paths=ToolPaths(
                creation_kit=Path("/fake/ck"),
                xedit=Path("/fake/xedit"),
                fallout4=fo4_path,
                archive2=Path("/fake/archive2")
            )
        )
        
        builder = PrevisBuilder(settings)
        
        # Mock archive wrapper to fail
        mock_archive = MagicMock()
        mock_archive.create_archive.return_value = False
        builder.archive_wrapper = mock_archive
        
        # Create precombined files
        precombined_path = data_path / "PreCombined"
        precombined_path.mkdir()
        (precombined_path / "test.nif").touch()
        
        result = builder._package_files()
        
        assert result is False
        mock_logger.error.assert_called_with("Failed to create main archive")


class TestCleanupExtended:
    """Test extended cleanup scenarios."""

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    @patch("PrevisLib.utils.file_system.clean_previs_files")
    def test_cleanup_success(self, mock_clean_files, mock_validate):
        """Test successful cleanup."""
        mock_validate.return_value = (True, "OK")
        mock_clean_files.return_value = (10, 3)  # 10 files, 3 archives deleted
        
        settings = Settings(
            plugin_name="test.esp",
            build_mode=BuildMode.CLEAN,
            tool_paths=ToolPaths(
                creation_kit=Path("/fake/ck"),
                xedit=Path("/fake/xedit"),
                fallout4=Path("/fake/fo4"),
                archive2=Path("/fake/archive2")
            )
        )
        
        builder = PrevisBuilder(settings)
        result = builder.cleanup()
        
        assert result is True
        mock_clean_files.assert_called_once()