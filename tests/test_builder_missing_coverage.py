"""Tests to improve coverage for remaining uncovered lines in builder.py."""

from enum import Enum
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from PrevisLib.config.settings import Settings
from PrevisLib.core.builder import PrevisBuilder
from PrevisLib.models.data_classes import BuildMode, BuildStep, ToolPaths


class TestBuilderValidationEdgeCases:
    """Test edge cases in builder validation."""

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    def test_init_no_creation_kit_path(self, mock_validate: MagicMock) -> None:  # noqa: ARG002
        """Test initialization when Creation Kit path is missing."""
        settings = Settings(
            plugin_name="test.esp",
            build_mode=BuildMode.CLEAN,
            tool_paths=ToolPaths(
                creation_kit=None,  # Missing
                xedit=Path("/fake/xedit"),
                fallout4=Path("/fake/fo4"),
                archive2=Path("/fake/archive2"),
            ),
        )

        with pytest.raises(ValueError, match="Creation Kit path is required but not configured"):
            PrevisBuilder(settings)

    def test_init_no_xedit_path(self) -> None:
        """Test initialization when xEdit path is missing."""
        settings = Settings(
            plugin_name="test.esp",
            build_mode=BuildMode.CLEAN,
            tool_paths=ToolPaths(
                creation_kit=Path("/fake/ck"),
                xedit=None,  # Missing
                fallout4=Path("/fake/fo4"),
                archive2=Path("/fake/archive2"),
            ),
        )

        with pytest.raises(ValueError, match="xEdit path is required but not configured"):
            PrevisBuilder(settings)

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    def test_init_no_fallout4_path(self, mock_validate: MagicMock) -> None:
        """Test initialization when Fallout 4 path is missing."""
        mock_validate.return_value = (True, "OK")

        settings = Settings(
            plugin_name="test.esp",
            build_mode=BuildMode.CLEAN,
            tool_paths=ToolPaths(
                creation_kit=Path("/fake/ck"),
                xedit=Path("/fake/xedit"),
                fallout4=None,  # Missing
                archive2=Path("/fake/archive2"),
            ),
        )

        with pytest.raises(ValueError, match="Fallout 4 path is required but not configured"):
            PrevisBuilder(settings)

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    def test_get_resume_options_with_failed_step(self, mock_validate: MagicMock) -> None:
        """Test get_resume_options when there's a failed step."""
        mock_validate.return_value = (True, "OK")

        settings = Settings(
            plugin_name="test.esp",
            build_mode=BuildMode.CLEAN,
            tool_paths=ToolPaths(
                creation_kit=Path("/fake/ck"), xedit=Path("/fake/xedit"), fallout4=Path("/fake/fo4"), archive2=Path("/fake/archive2")
            ),
        )

        builder = PrevisBuilder(settings)
        builder.failed_step = BuildStep.GENERATE_PREVIS

        resume_options = builder.get_resume_options()

        # Should offer to resume from failed step and all subsequent steps
        assert BuildStep.GENERATE_PREVIS in resume_options
        assert BuildStep.MERGE_PREVIS in resume_options
        assert BuildStep.FINAL_PACKAGING in resume_options

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    def test_get_steps_all_modes(self, mock_validate: MagicMock) -> None:
        """Test _get_steps for different build modes."""
        mock_validate.return_value = (True, "OK")

        # Test CLEAN mode
        settings = Settings(
            plugin_name="test.esp",
            build_mode=BuildMode.CLEAN,
            tool_paths=ToolPaths(
                creation_kit=Path("/fake/ck"), xedit=Path("/fake/xedit"), fallout4=Path("/fake/fo4"), archive2=Path("/fake/archive2")
            ),
        )

        builder = PrevisBuilder(settings)
        steps = builder._get_steps_to_run(start_from=None)

        # Should contain all steps
        assert steps == list(BuildStep)

    @patch("PrevisLib.core.builder.logger")
    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    def test_build_resume_with_invalid_step(self, mock_validate: MagicMock, mock_logger: MagicMock) -> None:
        """Test build with invalid start_from_step."""
        mock_validate.return_value = (True, "OK")

        settings = Settings(
            plugin_name="test.esp",
            build_mode=BuildMode.FILTERED,  # Filtered mode
            tool_paths=ToolPaths(
                creation_kit=Path("/fake/ck"), xedit=Path("/fake/xedit"), fallout4=Path("/fake/fo4"), archive2=Path("/fake/archive2")
            ),
        )

        builder = PrevisBuilder(settings)

        # Try to resume from a step that doesn't exist
        class DummyStep(Enum):
            INVALID_STEP = 99

        with patch.object(builder, "_execute_step", return_value=True):
            result = builder.build(start_from_step=DummyStep.INVALID_STEP)  # type: ignore

        assert result is True  # Should succeed but run all steps
        mock_logger.warning.assert_called_with(f"Invalid start step: {DummyStep.INVALID_STEP}, running all steps")


class TestPackageFilesEdgeCases:
    """Test additional edge cases in _package_files."""

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    @patch("PrevisLib.core.builder.logger")
    def test_package_files_create_archive_fails(self, mock_logger: MagicMock, mock_validate: MagicMock, tmp_path: Path) -> None:  # noqa: ARG002
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
                creation_kit=Path("/fake/ck"), xedit=Path("/fake/xedit"), fallout4=fo4_path, archive2=Path("/fake/archive2")
            ),
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

        result = builder._step_archive_meshes()

        assert result is False


class TestCleanupExtended:
    """Test extended cleanup scenarios."""

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    @patch("PrevisLib.core.builder.fs.clean_directory")
    @patch("PrevisLib.core.builder.fs.safe_delete")
    def test_cleanup_success(
        self, mock_safe_delete: MagicMock, mock_clean_dir: MagicMock, mock_validate: MagicMock, tmp_path: Path
    ) -> None:
        """Test successful cleanup."""
        mock_validate.return_value = (True, "OK")
        mock_safe_delete.return_value = True

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

        # Create dummy files and directories to be cleaned
        (builder.data_path / f"{builder.plugin_base_name} - Main.ba2").touch()
        builder.output_path.mkdir(exist_ok=True)

        result = builder.cleanup()

        assert result is True
        mock_safe_delete.assert_called()
        mock_clean_dir.assert_called()
