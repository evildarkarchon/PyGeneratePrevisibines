"""Tests for edge cases and error handling in PrevisBuilder."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from PrevisLib.core.builder import PrevisBuilder
from PrevisLib.config.settings import Settings
from PrevisLib.models.data_classes import ArchiveTool, BuildMode, BuildStep, ToolPaths


class TestPrevisBuilderInitialization:
    """Test PrevisBuilder initialization edge cases."""

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    def test_init_with_bsarch_missing_path(self, mock_validate):
        """Test initialization when BSArch is selected but path is missing."""
        mock_validate.return_value = (True, "OK")
        
        settings = Settings(
            plugin_name="test.esp",
            build_mode=BuildMode.CLEAN,
            archive_tool=ArchiveTool.BSARCH,
            tool_paths=ToolPaths(
                creation_kit=Path("/fake/ck"),
                xedit=Path("/fake/xedit"),
                fallout4=Path("/fake/fo4"),
                archive2=Path("/fake/archive2"),
                bsarch=None  # Missing BSArch path
            )
        )
        
        with pytest.raises(ValueError, match="BSArch path is required but not configured"):
            PrevisBuilder(settings)

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    def test_init_with_archive2_missing_path(self, mock_validate):
        """Test initialization when Archive2 is selected but path is missing."""
        mock_validate.return_value = (True, "OK")
        
        settings = Settings(
            plugin_name="test.esp",
            build_mode=BuildMode.CLEAN,
            archive_tool=ArchiveTool.ARCHIVE2,
            tool_paths=ToolPaths(
                creation_kit=Path("/fake/ck"),
                xedit=Path("/fake/xedit"),
                fallout4=Path("/fake/fo4"),
                archive2=None,  # Missing Archive2 path
                bsarch=Path("/fake/bsarch")
            )
        )
        
        with pytest.raises(ValueError, match="Archive2 path is required but not configured"):
            PrevisBuilder(settings)

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    def test_init_with_invalid_plugin_extension(self, mock_validate):
        """Test initialization with invalid plugin extension."""
        mock_validate.return_value = (True, "OK")
        
        settings = Settings(
            plugin_name="test.txt",  # Invalid extension
            build_mode=BuildMode.CLEAN,
            tool_paths=ToolPaths(
                creation_kit=Path("/fake/ck"),
                xedit=Path("/fake/xedit"),
                fallout4=Path("/fake/fo4"),
                archive2=Path("/fake/archive2")
            )
        )
        
        builder = PrevisBuilder(settings)
        with pytest.raises(ValueError, match="Invalid plugin extension"):
            builder._get_plugin_base_name()


class TestXEditScriptFinding:
    """Test xEdit script finding functionality."""

    def test_find_xedit_script_no_xedit_path(self):
        """Test finding script when xEdit path is not configured."""
        settings = Settings(
            plugin_name="test.esp",
            build_mode=BuildMode.CLEAN,
            tool_paths=ToolPaths(
                creation_kit=Path("/fake/ck"),
                xedit=None,  # No xEdit path
                fallout4=Path("/fake/fo4"),
                archive2=Path("/fake/archive2")
            )
        )
        
        builder = PrevisBuilder(settings)
        
        with pytest.raises(ValueError, match="xEdit path is required but not configured"):
            builder._find_xedit_script("test_script.pas")

    def test_find_xedit_script_not_found(self, tmp_path):
        """Test finding script that doesn't exist."""
        fo4_path = tmp_path / "Fallout4"
        fo4_path.mkdir()
        xedit_path = tmp_path / "xEdit" / "FO4Edit.exe"
        xedit_path.parent.mkdir()
        xedit_path.touch()
        
        settings = Settings(
            plugin_name="test.esp",
            build_mode=BuildMode.CLEAN,
            tool_paths=ToolPaths(
                creation_kit=Path("/fake/ck"),
                xedit=xedit_path,
                fallout4=fo4_path,
                archive2=Path("/fake/archive2")
            )
        )
        
        builder = PrevisBuilder(settings)
        result = builder._find_xedit_script("missing_script.pas")
        
        assert result is None

    def test_find_xedit_script_found(self, tmp_path):
        """Test successfully finding a script."""
        fo4_path = tmp_path / "Fallout4"
        fo4_path.mkdir()
        data_path = fo4_path / "Data"
        data_path.mkdir()
        
        xedit_path = tmp_path / "xEdit" / "FO4Edit.exe"
        xedit_path.parent.mkdir()
        xedit_path.touch()
        
        # Create script in xEdit's Edit Scripts folder
        scripts_dir = xedit_path.parent / "Edit Scripts"
        scripts_dir.mkdir()
        script_file = scripts_dir / "test_script.pas"
        script_file.touch()
        
        settings = Settings(
            plugin_name="test.esp",
            build_mode=BuildMode.CLEAN,
            tool_paths=ToolPaths(
                creation_kit=Path("/fake/ck"),
                xedit=xedit_path,
                fallout4=fo4_path,
                archive2=Path("/fake/archive2")
            )
        )
        
        builder = PrevisBuilder(settings)
        result = builder._find_xedit_script("test_script.pas")
        
        assert result == script_file


class TestPackageFiles:
    """Test _package_files method edge cases."""

    @patch("PrevisLib.core.builder.logger")
    def test_package_files_no_visibility_files(self, mock_logger, tmp_path):
        """Test packaging when no visibility files are found."""
        # Setup
        fo4_path = tmp_path / "Fallout4"
        data_path = fo4_path / "Data"
        data_path.mkdir(parents=True)
        temp_path = data_path / "Temp"
        temp_path.mkdir()
        
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
        
        # Mock archive wrapper
        mock_archive = MagicMock()
        mock_archive.create_archive.return_value = True
        mock_archive.add_to_archive.return_value = True
        builder.archive_wrapper = mock_archive
        
        # Create precombined files but no visibility files
        precombined_path = data_path / "PreCombined"
        precombined_path.mkdir()
        (precombined_path / "test.nif").touch()
        
        result = builder._package_files()
        
        assert result is True
        mock_logger.warning.assert_called_with("No visibility files found to add to archive")

    @patch("PrevisLib.core.builder.logger")
    def test_package_files_add_to_archive_fails(self, mock_logger, tmp_path):
        """Test packaging when adding to archive fails."""
        # Setup
        fo4_path = tmp_path / "Fallout4"
        data_path = fo4_path / "Data"
        data_path.mkdir(parents=True)
        temp_path = data_path / "Temp"
        temp_path.mkdir()
        vis_path = data_path / "Vis"
        vis_path.mkdir()
        
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
        
        # Mock archive wrapper
        mock_archive = MagicMock()
        mock_archive.create_archive.return_value = True
        mock_archive.add_to_archive.return_value = False  # Fail to add
        builder.archive_wrapper = mock_archive
        
        # Create files
        precombined_path = data_path / "PreCombined"
        precombined_path.mkdir()
        (precombined_path / "test.nif").touch()
        (vis_path / "test.uvd").touch()
        
        result = builder._package_files()
        
        assert result is False
        mock_logger.error.assert_called_with("Failed to add visibility data to archive")

    @patch("PrevisLib.core.builder.logger")
    def test_package_files_no_main_archive(self, mock_logger, tmp_path):
        """Test packaging when main archive is not created."""
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
        
        # Mock archive wrapper
        mock_archive = MagicMock()
        mock_archive.create_archive.return_value = True
        builder.archive_wrapper = mock_archive
        
        # Create precombined files
        precombined_path = data_path / "PreCombined"
        precombined_path.mkdir()
        (precombined_path / "test.nif").touch()
        
        # Main archive doesn't exist after creation
        result = builder._package_files()
        
        assert result is False
        mock_logger.error.assert_called_with("Main archive not found")


class TestCleanupMethods:
    """Test cleanup method edge cases."""

    @patch("PrevisLib.core.builder.PrevisFileCleaner")
    def test_cleanup_with_error(self, mock_cleaner_class):
        """Test cleanup when cleaner raises exception."""
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
        
        mock_cleaner = MagicMock()
        mock_cleaner.cleanup.side_effect = Exception("Cleanup failed")
        mock_cleaner_class.return_value = mock_cleaner
        
        # Should not raise, just return False
        result = builder.cleanup()
        
        assert result is False

    @patch("PrevisLib.utils.file_system.clean_directory")
    @patch("PrevisLib.core.builder.logger")
    def test_cleanup_working_files_error(self, mock_logger, mock_clean_dir):
        """Test cleanup_working_files when directory cleaning fails."""
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
        
        mock_clean_dir.side_effect = Exception("Permission denied")
        
        # Should not raise, just return False
        result = builder.cleanup_working_files()
        
        assert result is False
        mock_logger.error.assert_called()


class TestBuildProcessEdgeCases:
    """Test edge cases in the build process."""

    @patch("PrevisLib.core.builder.BuildStepExecutor")
    def test_build_with_failed_step(self, mock_executor_class):
        """Test build process when a step fails."""
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
        
        # Mock executor to fail on second step
        mock_executor = MagicMock()
        mock_executor.execute_steps.return_value = (False, BuildStep.GENERATE_VISIBILITY)
        mock_executor_class.return_value = mock_executor
        
        result = builder.build()
        
        assert result is False
        assert builder.failed_step == BuildStep.GENERATE_VISIBILITY

    @patch("PrevisLib.core.builder.BuildStepExecutor")
    @patch("PrevisLib.core.builder.logger")
    def test_build_with_start_from_step(self, mock_logger, mock_executor_class):
        """Test building from a specific step."""
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
        
        mock_executor = MagicMock()
        mock_executor.execute_steps.return_value = (True, None)
        mock_executor_class.return_value = mock_executor
        
        result = builder.build(start_from_step=BuildStep.GENERATE_VISIBILITY)
        
        assert result is True
        mock_logger.info.assert_any_call("Resuming from step: GENERATE_VISIBILITY")