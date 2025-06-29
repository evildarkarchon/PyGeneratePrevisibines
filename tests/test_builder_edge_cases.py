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
                bsarch=None,  # Missing BSArch path
            ),
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
                bsarch=Path("/fake/bsarch"),
            ),
        )

        with pytest.raises(ValueError, match="Archive2 path is required but not configured"):
            PrevisBuilder(settings)

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    def test_init_with_invalid_plugin_extension(self, mock_validate):
        """Test initialization with invalid plugin extension."""
        mock_validate.return_value = (True, "OK")

        with pytest.raises(ValueError, match="Invalid plugin extension"):
            Settings(
                plugin_name="test.txt",  # Invalid extension
                build_mode=BuildMode.CLEAN,
                tool_paths=ToolPaths(
                    creation_kit=Path("/fake/ck"), xedit=Path("/fake/xedit"), fallout4=Path("/fake/fo4"), archive2=Path("/fake/archive2")
                ),
            )


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
                archive2=Path("/fake/archive2"),
            ),
        )

        with pytest.raises(ValueError, match="xEdit path is required but not configured"):
            PrevisBuilder(settings)

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    def test_find_xedit_script_not_found(self, mock_validate, tmp_path):
        """Test finding script that doesn't exist."""
        mock_validate.return_value = (True, "OK")
        fo4_path = tmp_path / "Fallout4"
        fo4_path.mkdir()
        xedit_path = tmp_path / "xEdit" / "FO4Edit.exe"
        xedit_path.parent.mkdir()
        xedit_path.touch()

        settings = Settings(
            plugin_name="test.esp",
            build_mode=BuildMode.CLEAN,
            tool_paths=ToolPaths(creation_kit=Path("/fake/ck"), xedit=xedit_path, fallout4=fo4_path, archive2=Path("/fake/archive2")),
        )

        builder = PrevisBuilder(settings)
        result = builder._find_xedit_script("missing_script.pas")

        assert result is None

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    def test_find_xedit_script_found(self, mock_validate, tmp_path):
        """Test successfully finding a script."""
        mock_validate.return_value = (True, "OK")
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
            tool_paths=ToolPaths(creation_kit=Path("/fake/ck"), xedit=xedit_path, fallout4=fo4_path, archive2=Path("/fake/archive2")),
        )

        builder = PrevisBuilder(settings)
        result = builder._find_xedit_script("test_script")

        assert result == script_file


class TestPackageFiles:
    """Test _package_files method edge cases."""

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    @patch("PrevisLib.core.builder.logger")
    def test_package_files_no_visibility_files(self, mock_logger, mock_validate, tmp_path):
        """Test packaging when no visibility files are found."""
        mock_validate.return_value = (True, "OK")
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
                creation_kit=Path("/fake/ck"), xedit=Path("/fake/xedit"), fallout4=fo4_path, archive2=Path("/fake/archive2")
            ),
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

        # Create the main archive (which would have been created in step 3)
        main_archive_path = data_path / "test - Main.ba2"
        main_archive_path.touch()

        result = builder._step_final_packaging()

        assert result is True
        mock_logger.warning.assert_called_with("No visibility files found to add to archive")

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    @patch("PrevisLib.core.builder.logger")
    def test_package_files_add_to_archive_fails(self, mock_logger, mock_validate, tmp_path):
        """Test packaging when adding to archive fails."""
        mock_validate.return_value = (True, "OK")
        # Setup
        fo4_path = tmp_path / "Fallout4"
        data_path = fo4_path / "Data"
        data_path.mkdir(parents=True)
        temp_path = data_path / "Temp"
        temp_path.mkdir()
        (temp_path / "test.uvd").touch()  # Create a dummy visibility file

        # Main archive must exist for this step
        main_archive_path = data_path / "test - Main.ba2"  # Use plugin base name, not full plugin name
        main_archive_path.touch()

        settings = Settings(
            plugin_name="test.esp",
            build_mode=BuildMode.CLEAN,
            tool_paths=ToolPaths(
                creation_kit=Path("/fake/ck"), xedit=Path("/fake/xedit"), fallout4=fo4_path, archive2=Path("/fake/archive2")
            ),
        )

        builder = PrevisBuilder(settings)

        # Mock archive wrapper
        mock_archive = MagicMock()
        mock_archive.add_to_archive.return_value = False  # Fail to add
        builder.archive_wrapper = mock_archive

        result = builder._step_final_packaging()

        assert result is False
        mock_logger.error.assert_called_with("Failed to add visibility data to archive")

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    @patch("PrevisLib.core.builder.logger")
    def test_package_files_no_main_archive(self, mock_logger, mock_validate, tmp_path):
        """Test packaging when main archive is not created."""
        mock_validate.return_value = (True, "OK")
        # Setup
        fo4_path = tmp_path / "Fallout4"
        data_path = fo4_path / "Data"
        data_path.mkdir(parents=True)
        temp_path = data_path / "Temp"
        temp_path.mkdir()
        (temp_path / "test.uvd").touch()

        settings = Settings(
            plugin_name="test.esp",
            build_mode=BuildMode.CLEAN,
            tool_paths=ToolPaths(
                creation_kit=Path("/fake/ck"), xedit=Path("/fake/xedit"), fallout4=fo4_path, archive2=Path("/fake/archive2")
            ),
        )

        builder = PrevisBuilder(settings)

        # Main archive does not exist
        result = builder._step_final_packaging()

        assert result is False
        main_archive_path = builder.data_path / f"{builder.plugin_base_name} - Main.ba2"
        mock_logger.error.assert_called_with(f"Main archive not found: {main_archive_path}")


class TestCleanupMethods:
    """Test cleanup method edge cases."""

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    @patch("PrevisLib.core.builder.fs.safe_delete", side_effect=OSError("Permission denied"))
    def test_cleanup_with_error(self, mock_safe_delete, mock_validate, tmp_path):
        """Test cleanup when cleaner raises exception."""
        mock_validate.return_value = (True, "OK")

        fo4_path = tmp_path / "Fallout4"
        data_path = fo4_path / "Data"
        data_path.mkdir(parents=True)

        settings = Settings(
            plugin_name="test.esp",
            build_mode=BuildMode.CLEAN,
            tool_paths=ToolPaths(
                creation_kit=Path("/fake/ck"), xedit=Path("/fake/xedit"), fallout4=fo4_path, archive2=Path("/fake/archive2")
            ),
        )

        builder = PrevisBuilder(settings)
        # Create a dummy file to be cleaned up to trigger the mock
        (builder.data_path / "test - Main.ba2").touch()

        # Should not raise, just return False
        result = builder.cleanup()

        assert result is False

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    @patch("PrevisLib.core.builder.fs.safe_delete")
    @patch("PrevisLib.core.builder.logger")
    def test_cleanup_working_files_error(self, mock_logger, mock_safe_delete, mock_validate, tmp_path):
        """Test cleanup_working_files when directory cleaning fails."""
        mock_validate.return_value = (True, "OK")

        fo4_path = tmp_path / "Fallout4"
        fo4_path.mkdir()

        settings = Settings(
            plugin_name="test.esp",
            build_mode=BuildMode.CLEAN,
            tool_paths=ToolPaths(
                creation_kit=Path("/fake/ck"), xedit=Path("/fake/xedit"), fallout4=fo4_path, archive2=Path("/fake/archive2")
            ),
        )

        builder = PrevisBuilder(settings)
        (builder.data_path).mkdir()
        (builder.data_path / "CombinedObjects.esp").touch()

        mock_safe_delete.return_value = False

        # Should not raise, just return False
        result = builder.cleanup_working_files()

        assert result is False
        mock_logger.error.assert_called()


class TestBuildProcessEdgeCases:
    """Test edge cases in the build process."""

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    def test_build_with_failed_step(self, mock_validate):
        """Test build process when a step fails."""
        mock_validate.return_value = (True, "OK")
        settings = Settings(
            plugin_name="test.esp",
            build_mode=BuildMode.CLEAN,
            tool_paths=ToolPaths(
                creation_kit=Path("/fake/ck"), xedit=Path("/fake/xedit"), fallout4=Path("/fake/fo4"), archive2=Path("/fake/archive2")
            ),
        )

        builder = PrevisBuilder(settings)

        # Mock a step to fail
        with patch.object(builder, "_execute_step") as mock_execute_step:
            mock_execute_step.side_effect = [True, False]  # First step succeeds, second fails

            result = builder.build()

        assert result is False
        assert builder.failed_step == BuildStep.MERGE_COMBINED_OBJECTS

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    @patch("PrevisLib.core.builder.logger")
    def test_build_with_start_from_step(self, mock_logger, mock_validate):
        """Test building from a specific step."""
        mock_validate.return_value = (True, "OK")
        settings = Settings(
            plugin_name="test.esp",
            build_mode=BuildMode.CLEAN,
            tool_paths=ToolPaths(
                creation_kit=Path("/fake/ck"), xedit=Path("/fake/xedit"), fallout4=Path("/fake/fo4"), archive2=Path("/fake/archive2")
            ),
        )

        builder = PrevisBuilder(settings)

        with patch.object(builder, "_execute_step", return_value=True) as mock_execute_step:
            result = builder.build(start_from_step=BuildStep.GENERATE_PREVIS)

            assert result is True
            mock_execute_step.assert_called()
            # Check that steps before the start_from_step were not executed
            assert mock_execute_step.call_count == len(list(BuildStep)) - list(BuildStep).index(BuildStep.GENERATE_PREVIS)
