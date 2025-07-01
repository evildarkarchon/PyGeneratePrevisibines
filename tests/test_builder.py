"""Consolidated tests for PrevisBuilder core orchestration, edge cases, and build steps."""

from enum import Enum
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch
import time

import pytest

from PrevisLib.config.settings import Settings
from PrevisLib.core.builder import PrevisBuilder
from PrevisLib.core.build_steps import BuildStepExecutor
from PrevisLib.models.data_classes import ArchiveTool, BuildMode, BuildStep, ToolPaths


class TestPrevisBuilder:
    """Test PrevisBuilder class."""

    @pytest.fixture
    def mock_settings(self, tmp_path: Path) -> Settings:
        """Create mock settings for testing."""
        settings = Settings()
        settings.plugin_name = "TestMod.esp"
        settings.build_mode = BuildMode.CLEAN
        settings.working_directory = tmp_path
        settings.tool_paths = ToolPaths(
            creation_kit=tmp_path / "CreationKit.exe",
            xedit=tmp_path / "xEdit.exe",
            fallout4=tmp_path / "Fallout4.exe",
            archive2=tmp_path / "Archive2.exe",
        )

        # Create fake tool files
        for tool_path in [
            settings.tool_paths.creation_kit,
            settings.tool_paths.xedit,
            settings.tool_paths.fallout4,
            settings.tool_paths.archive2,
        ]:
            tool_path.parent.mkdir(parents=True, exist_ok=True)  # type: ignore[reportOptionalMemberAccess, union-attr]
            tool_path.write_text("fake tool")  # type: ignore[reportOptionalMemberAccess, union-attr]

        return settings

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    def test_initialization_success(self, mock_validate_scripts: MagicMock, mock_settings: Settings) -> None:
        """Test successful PrevisBuilder initialization."""
        mock_validate_scripts.return_value = (True, "Scripts validated")

        builder = PrevisBuilder(mock_settings)

        assert builder.plugin_name == "TestMod.esp"
        assert builder.build_mode == BuildMode.CLEAN
        assert builder.settings == mock_settings
        assert builder.completed_steps == []
        assert builder.failed_step is None

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    def test_initialization_missing_creation_kit(self, mock_validate_scripts: MagicMock, mock_settings: Settings) -> None:
        """Test initialization fails with missing Creation Kit."""
        mock_validate_scripts.return_value = (True, "Scripts validated")
        mock_settings.tool_paths.creation_kit = None

        with pytest.raises(ValueError, match="Creation Kit path is required"):
            PrevisBuilder(mock_settings)

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    def test_initialization_missing_xedit(self, mock_validate_scripts: MagicMock, mock_settings: Settings) -> None:
        """Test initialization fails with missing xEdit."""
        mock_validate_scripts.return_value = (True, "Scripts validated")
        mock_settings.tool_paths.xedit = None

        with pytest.raises(ValueError, match="xEdit path is required"):
            PrevisBuilder(mock_settings)

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    def test_initialization_missing_fallout4(self, mock_validate_scripts: MagicMock, mock_settings: Settings) -> None:
        """Test initialization fails with missing Fallout 4."""
        mock_validate_scripts.return_value = (True, "Scripts validated")
        mock_settings.tool_paths.fallout4 = None

        with pytest.raises(ValueError, match="Fallout 4 path is required"):
            PrevisBuilder(mock_settings)

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    def test_get_plugin_base_name(self, mock_validate_scripts: MagicMock, mock_settings: Settings) -> None:
        """Test plugin base name extraction."""
        mock_validate_scripts.return_value = (True, "Scripts validated")
        builder = PrevisBuilder(mock_settings)

        assert builder._get_plugin_base_name() == "TestMod"

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    def test_get_steps_to_run_all_steps(self, mock_validate_scripts: MagicMock, mock_settings: Settings) -> None:
        """Test getting all steps when no start point specified."""
        mock_validate_scripts.return_value = (True, "Scripts validated")
        builder = PrevisBuilder(mock_settings)

        steps = builder._get_steps_to_run(None)

        assert steps == list(BuildStep)
        assert len(steps) == 8

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    def test_get_steps_to_run_from_middle(self, mock_validate_scripts: MagicMock, mock_settings: Settings) -> None:
        """Test getting steps from middle of process."""
        mock_validate_scripts.return_value = (True, "Scripts validated")
        builder = PrevisBuilder(mock_settings)

        steps = builder._get_steps_to_run(BuildStep.COMPRESS_PSG)

        expected_steps = [
            BuildStep.COMPRESS_PSG,
            BuildStep.BUILD_CDX,
            BuildStep.GENERATE_PREVIS,
            BuildStep.MERGE_PREVIS,
            BuildStep.FINAL_PACKAGING,
        ]
        assert steps == expected_steps

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    def test_get_steps_to_run_invalid_step(self, mock_validate_scripts: MagicMock, mock_settings: Settings) -> None:
        """Test getting steps with invalid start step."""
        mock_validate_scripts.return_value = (True, "Scripts validated")
        builder = PrevisBuilder(mock_settings)

        # Mock an invalid step that's not in the enum
        with patch("PrevisLib.core.builder.logger") as mock_logger:
            steps = builder._get_steps_to_run("invalid_step")  # type: ignore[arg-type]

            assert steps == list(BuildStep)
            mock_logger.warning.assert_called_once()

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    @patch("PrevisLib.core.builder.datetime")
    def test_build_success_all_steps(self, mock_datetime: MagicMock, mock_validate_scripts: MagicMock, mock_settings: Settings) -> None:
        """Test successful build execution of all steps."""
        mock_validate_scripts.return_value = (True, "Scripts validated")
        mock_datetime.now.return_value.strftime.return_value = "2023-01-01 12:00:00"

        builder = PrevisBuilder(mock_settings)

        # Mock all step methods to return True
        step_methods = [
            "_step_generate_precombined",
            "_step_merge_combined_objects",
            "_step_archive_meshes",
            "_step_compress_psg",
            "_step_build_cdx",
            "_step_generate_previs",
            "_step_merge_previs",
            "_step_final_packaging",
        ]

        for method_name in step_methods:
            setattr(builder, method_name, Mock(return_value=True))

        with patch("PrevisLib.core.builder.logger"):
            result = builder.build()

        assert result is True
        assert len(builder.completed_steps) == 8
        assert builder.failed_step is None

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    @patch("PrevisLib.core.builder.datetime")
    def test_build_failure_at_step(self, mock_datetime: MagicMock, mock_validate_scripts: MagicMock, mock_settings: Settings) -> None:
        """Test build failure at specific step."""
        mock_validate_scripts.return_value = (True, "Scripts validated")
        mock_datetime.now.return_value.strftime.return_value = "2023-01-01 12:00:00"

        builder = PrevisBuilder(mock_settings)

        # Mock first step to succeed, second to fail
        builder._step_generate_precombined = Mock(return_value=True)  # type: ignore[method-assign]
        builder._step_merge_combined_objects = Mock(return_value=False)  # type: ignore[method-assign]

        with patch("PrevisLib.core.builder.logger"):
            result = builder.build()

        assert result is False
        assert len(builder.completed_steps) == 1
        assert builder.failed_step == BuildStep.MERGE_COMBINED_OBJECTS

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    @patch("PrevisLib.core.builder.datetime")
    def test_build_exception_during_step(self, mock_datetime: MagicMock, mock_validate_scripts: MagicMock, mock_settings: Settings) -> None:
        """Test build handles exception during step execution."""
        mock_validate_scripts.return_value = (True, "Scripts validated")
        mock_datetime.now.return_value.strftime.return_value = "2023-01-01 12:00:00"

        builder = PrevisBuilder(mock_settings)

        # Mock first step to raise exception
        builder._step_generate_precombined = Mock(side_effect=Exception("Test error"))  # type: ignore[method-assign]

        with patch("PrevisLib.core.builder.logger"):
            result = builder.build()

        assert result is False
        assert len(builder.completed_steps) == 0
        assert builder.failed_step == BuildStep.GENERATE_PRECOMBINED

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    def test_build_keyboard_interrupt(self, mock_validate_scripts: MagicMock, mock_settings: Settings) -> None:
        """Test build handles keyboard interrupt properly."""
        mock_validate_scripts.return_value = (True, "Scripts validated")
        builder = PrevisBuilder(mock_settings)

        # Mock first step to raise KeyboardInterrupt
        builder._step_generate_precombined = Mock(side_effect=KeyboardInterrupt())  # type: ignore[method-assign]

        with patch("PrevisLib.core.builder.logger"), pytest.raises(KeyboardInterrupt):
            builder.build()

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    def test_execute_step_success(self, mock_validate_scripts: MagicMock, mock_settings: Settings) -> None:
        """Test successful step execution."""
        mock_validate_scripts.return_value = (True, "Scripts validated")
        builder = PrevisBuilder(mock_settings)
        builder._step_generate_precombined = Mock(return_value=True)  # type: ignore[method-assign]

        result = builder._execute_step(BuildStep.GENERATE_PRECOMBINED)

        assert result is True
        builder._step_generate_precombined.assert_called_once()

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    def test_execute_step_unknown(self, mock_validate_scripts: MagicMock, mock_settings: Settings) -> None:
        """Test execution of unknown step."""
        mock_validate_scripts.return_value = (True, "Scripts validated")
        builder = PrevisBuilder(mock_settings)

        # Create a mock step that doesn't exist in the step map
        unknown_step = Mock()
        unknown_step.name = "UNKNOWN_STEP"

        with patch("PrevisLib.core.builder.logger") as mock_logger:
            result = builder._execute_step(unknown_step)

        assert result is False
        mock_logger.error.assert_called_once()

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    def test_get_resume_options_no_failure(self, mock_validate_scripts: MagicMock, mock_settings: Settings) -> None:
        """Test resume options when no failure occurred."""
        mock_validate_scripts.return_value = (True, "Scripts validated")
        builder = PrevisBuilder(mock_settings)

        options = builder.get_resume_options()

        assert options == list(BuildStep)

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    def test_get_resume_options_with_failure(self, mock_validate_scripts: MagicMock, mock_settings: Settings) -> None:
        """Test resume options when failure occurred."""
        mock_validate_scripts.return_value = (True, "Scripts validated")
        builder = PrevisBuilder(mock_settings)
        builder.failed_step = BuildStep.COMPRESS_PSG

        options = builder.get_resume_options()

        expected_options = [
            BuildStep.COMPRESS_PSG,
            BuildStep.BUILD_CDX,
            BuildStep.GENERATE_PREVIS,
            BuildStep.MERGE_PREVIS,
            BuildStep.FINAL_PACKAGING,
        ]
        assert options == expected_options

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    def test_find_xedit_script_found(self, mock_validate_scripts: MagicMock, mock_settings: Settings, tmp_path: Path) -> None:
        """Test finding xEdit script successfully."""
        mock_validate_scripts.return_value = (True, "Scripts validated")
        builder = PrevisBuilder(mock_settings)
        builder.settings.tool_paths.xedit = tmp_path / "xEdit.exe"

        # Create script directory and file
        script_dir = tmp_path / "Edit Scripts"
        script_dir.mkdir()
        script_file = script_dir / "Merge Combined Objects.pas"
        script_file.write_text("script content")

        result = builder._find_xedit_script("Merge Combined Objects")

        assert result == script_file

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    def test_find_xedit_script_not_found(self, mock_validate_scripts: MagicMock, mock_settings: Settings) -> None:
        """Test finding xEdit script when not found."""
        mock_validate_scripts.return_value = (True, "Scripts validated")
        builder = PrevisBuilder(mock_settings)

        result = builder._find_xedit_script("Nonexistent Script")

        assert result is None

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
    def test_init_with_bsarch_missing_path(self, mock_validate: MagicMock) -> None:
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
    def test_init_with_archive2_missing_path(self, mock_validate: MagicMock) -> None:
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
    def test_init_with_invalid_plugin_extension(self, mock_validate: MagicMock) -> None:
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


class TestPrevisBuilderStepMethods:
    """Test individual step methods of PrevisBuilder."""

    @pytest.fixture
    def builder_with_mocks(self, tmp_path: Path) -> PrevisBuilder:
        """Create builder with mocked dependencies."""
        settings = Settings()
        settings.plugin_name = "TestMod.esp"
        settings.tool_paths = ToolPaths(
            creation_kit=tmp_path / "CreationKit.exe",
            xedit=tmp_path / "xEdit.exe",
            fallout4=tmp_path / "Fallout4.exe",
            archive2=tmp_path / "Archive2.exe",
        )

        # Create fake tool files
        for tool_path in [
            settings.tool_paths.creation_kit,
            settings.tool_paths.xedit,
            settings.tool_paths.fallout4,
            settings.tool_paths.archive2,
        ]:
            tool_path.parent.mkdir(parents=True, exist_ok=True)  # type: ignore[reportOptionalMemberAccess, union-attr]
            tool_path.write_text("fake tool")  # type: ignore[reportOptionalMemberAccess, union-attr]

        with patch("PrevisLib.core.builder.validate_xedit_scripts") as mock_validate_scripts:
            mock_validate_scripts.return_value = (True, "Scripts validated")
            builder = PrevisBuilder(settings)

        # Mock tool wrappers
        builder.ck_wrapper = Mock()
        builder.xedit_wrapper = Mock()
        builder.archive_wrapper = Mock()

        # Set up paths
        builder.data_path = tmp_path / "Data"
        builder.output_path = tmp_path / "Output"
        builder.temp_path = tmp_path / "Temp"

        return builder

    @patch("PrevisLib.core.builder.fs")
    def test_step_generate_precombined_success(self, mock_fs: MagicMock, builder_with_mocks: PrevisBuilder) -> None:
        """Test successful precombined generation step."""
        builder = builder_with_mocks
        builder.ck_wrapper.generate_precombined.return_value = True
        builder.output_path = Path("/fake/output")
        builder.data_path = Path("/fake/data")

        mock_fs.count_files.return_value = 5
        mock_fs.wait_for_output_file.return_value = True

        with patch("PrevisLib.core.builder.logger"):
            result = builder._step_generate_precombined()

        assert result is True
        mock_fs.clean_directory.assert_called_once_with(builder.output_path)
        builder.ck_wrapper.generate_precombined.assert_called_once_with(builder.data_path)

    @patch("PrevisLib.core.builder.fs")
    def test_step_generate_precombined_no_meshes(self, mock_fs: MagicMock, builder_with_mocks: PrevisBuilder) -> None:
        """Test precombined generation step when no meshes generated."""
        builder = builder_with_mocks
        builder.ck_wrapper.generate_precombined.return_value = True
        builder.output_path = Path("/fake/output")

        mock_fs.count_files.return_value = 0  # No meshes generated

        with patch("PrevisLib.core.builder.logger"):
            result = builder._step_generate_precombined()

        assert result is False

    @patch("PrevisLib.core.builder.fs")
    def test_step_merge_combined_objects_success(self, mock_fs: MagicMock, builder_with_mocks: PrevisBuilder) -> None:  # noqa: ARG002
        """Test successful merge combined objects step."""
        builder = builder_with_mocks
        script_path = Path("/fake/script.pas")

        builder._find_xedit_script = Mock(return_value=script_path)  # type: ignore[method-assign]
        builder.xedit_wrapper.merge_combined_objects.return_value = True  # type: ignore[reportAttributeAccessIssue]

        with patch("PrevisLib.core.builder.logger"):
            result = builder._step_merge_combined_objects()

        assert result is True
        builder.xedit_wrapper.merge_combined_objects.assert_called_once_with(builder.data_path, script_path)  # type: ignore[reportAttributeAccessIssue]

    def test_step_merge_combined_objects_no_script(self, builder_with_mocks: PrevisBuilder) -> None:
        """Test merge combined objects step when script not found."""
        builder = builder_with_mocks
        builder._find_xedit_script = Mock(return_value=None)  # type: ignore[method-assign]

        with patch("PrevisLib.core.builder.logger"):
            result = builder._step_merge_combined_objects()

        assert result is False

    @patch("PrevisLib.core.builder.fs")
    def test_step_archive_meshes_success(self, mock_fs: MagicMock, builder_with_mocks: PrevisBuilder) -> None:
        """Test successful archive meshes step."""
        builder = builder_with_mocks
        builder.archive_wrapper.create_archive.return_value = True  # type: ignore[reportAttributeAccessIssue]

        with patch("PrevisLib.core.builder.logger"):
            result = builder._step_archive_meshes()

        assert result is True
        builder.archive_wrapper.create_archive.assert_called_once()  # type: ignore[reportAttributeAccessIssue]
        mock_fs.clean_directory.assert_called_once_with(builder.output_path, create=False)

    def test_step_compress_psg_success(self, builder_with_mocks: PrevisBuilder) -> None:
        """Test successful compress PSG step."""
        builder = builder_with_mocks
        builder.ck_wrapper.compress_psg.return_value = True  # type: ignore[reportAttributeAccessIssue]

        with patch("PrevisLib.core.builder.logger"):
            result = builder._step_compress_psg()

        assert result is True
        builder.ck_wrapper.compress_psg.assert_called_once_with(builder.data_path)  # type: ignore[reportAttributeAccessIssue]

    def test_step_build_cdx_success(self, builder_with_mocks: PrevisBuilder) -> None:
        """Test successful build CDX step."""
        builder = builder_with_mocks
        builder.ck_wrapper.build_cdx.return_value = True  # type: ignore[reportAttributeAccessIssue]

        with patch("PrevisLib.core.builder.logger"):
            result = builder._step_build_cdx()

        assert result is True
        builder.ck_wrapper.build_cdx.assert_called_once_with(builder.data_path)  # type: ignore[reportAttributeAccessIssue]

    @patch("PrevisLib.core.builder.fs")
    def test_step_generate_previs_success(self, mock_fs: MagicMock, builder_with_mocks: PrevisBuilder) -> None:
        """Test successful generate previs step."""
        builder = builder_with_mocks
        builder.ck_wrapper.generate_previs_data.return_value = True  # type: ignore[reportAttributeAccessIssue]

        mock_fs.count_files.return_value = 3
        mock_fs.wait_for_output_file.return_value = True

        with patch("PrevisLib.core.builder.logger"):
            result = builder._step_generate_previs()

        assert result is True
        mock_fs.clean_directory.assert_called_once_with(builder.temp_path)
        builder.ck_wrapper.generate_previs_data.assert_called_once_with(builder.data_path)  # type: ignore[reportAttributeAccessIssue]

    @patch("PrevisLib.core.builder.fs")
    def test_step_final_packaging_success(self, mock_fs: MagicMock, builder_with_mocks: PrevisBuilder) -> None:
        """Test successful final packaging step."""
        builder = builder_with_mocks
        builder.archive_wrapper.add_to_archive.return_value = True  # type: ignore[reportAttributeAccessIssue]

        # Mock main archive exists
        main_archive = builder.data_path / "TestMod - Main.ba2"
        main_archive.parent.mkdir(parents=True, exist_ok=True)
        main_archive.write_text("fake archive")

        # Mock temp path is empty (simpler test case)
        mock_fs.is_directory_empty.return_value = True

        with patch("PrevisLib.core.builder.logger"):
            result = builder._step_final_packaging()

        assert result is True
        # Should not call add_to_archive when temp is empty
        builder.archive_wrapper.add_to_archive.assert_not_called()  # type: ignore[reportAttributeAccessIssue]

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    @patch("PrevisLib.core.builder.fs.safe_delete", side_effect=OSError("Permission denied"))
    def test_cleanup_with_error(self, mock_safe_delete: MagicMock, mock_validate: MagicMock, tmp_path: Path) -> None:
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


class TestBuildStepExecutor:
    """Test BuildStepExecutor class."""

    @pytest.fixture
    def executor(self, tmp_path: Path) -> BuildStepExecutor:
        """Create BuildStepExecutor for testing."""
        fo4_path = tmp_path / "Fallout4"
        fo4_path.mkdir()
        (fo4_path / "Data").mkdir()

        return BuildStepExecutor("TestMod.esp", fo4_path, BuildMode.CLEAN)

    def test_initialization(self, executor: BuildStepExecutor, tmp_path: Path) -> None:
        """Test BuildStepExecutor initialization."""
        assert executor.plugin_name == "TestMod.esp"
        assert executor.plugin_base == "TestMod"
        assert executor.build_mode == BuildMode.CLEAN
        assert executor.fo4_path == tmp_path / "Fallout4"
        assert executor.data_path == tmp_path / "Fallout4" / "Data"

    def test_get_plugin_base_name_valid_esp(self) -> None:
        """Test plugin base name extraction for .esp file."""
        executor = BuildStepExecutor("MyMod.esp", Path("/fake"), BuildMode.CLEAN)
        assert executor.plugin_base == "MyMod"

    def test_get_plugin_base_name_valid_esm(self) -> None:
        """Test plugin base name extraction for .esm file."""
        executor = BuildStepExecutor("MyMod.esm", Path("/fake"), BuildMode.CLEAN)
        assert executor.plugin_base == "MyMod"

    def test_get_plugin_base_name_valid_esl(self) -> None:
        """Test plugin base name extraction for .esl file."""
        executor = BuildStepExecutor("MyMod.esl", Path("/fake"), BuildMode.CLEAN)
        assert executor.plugin_base == "MyMod"

    def test_get_plugin_base_name_invalid_extension(self) -> None:
        """Test plugin base name extraction with invalid extension."""
        with pytest.raises(ValueError, match="Invalid plugin extension"):
            BuildStepExecutor("MyMod.txt", Path("/fake"), BuildMode.CLEAN)

    def test_get_plugin_base_name_no_extension(self) -> None:
        """Test plugin base name extraction with no extension."""
        with pytest.raises(ValueError, match="Invalid plugin extension"):
            BuildStepExecutor("MyMod", Path("/fake"), BuildMode.CLEAN)

    @patch("PrevisLib.core.build_steps.fs")
    def test_validate_precombined_output_success(self, mock_fs: MagicMock, executor: BuildStepExecutor, tmp_path: Path) -> None:
        """Test successful precombined output validation."""
        output_path = tmp_path / "output"
        output_path.mkdir()

        # Create fake mesh files
        mesh_files = [output_path / "mesh1.nif", output_path / "mesh2.nif", output_path / "mesh3.nif"]

        for mesh_file in mesh_files:
            mesh_file.write_text("fake mesh data" * 100)  # Make it reasonably sized

        mock_fs.find_files.return_value = mesh_files

        with patch("PrevisLib.core.build_steps.logger"):
            result = executor.validate_precombined_output(output_path)

        assert result["valid"] is True
        assert result["mesh_count"] == 3
        assert result["total_size"] > 0
        assert result["errors"] == []

    @patch("PrevisLib.core.build_steps.fs")
    def test_validate_precombined_output_no_meshes(self, mock_fs: MagicMock, executor: BuildStepExecutor, tmp_path: Path) -> None:
        """Test precombined output validation with no meshes."""
        output_path = tmp_path / "output"
        output_path.mkdir()

        mock_fs.find_files.return_value = []

        result = executor.validate_precombined_output(output_path)

        assert result["valid"] is False
        assert result["mesh_count"] == 0
        assert "No mesh files generated" in result["errors"]

    def test_clean_mode(self, tmp_path: Path) -> None:
        """Test executor with clean build mode."""
        fo4_path = tmp_path / "Fallout4"
        fo4_path.mkdir()
        (fo4_path / "Data").mkdir()

        executor = BuildStepExecutor("TestMod.esp", fo4_path, BuildMode.CLEAN)

        assert executor.build_mode == BuildMode.CLEAN

    def test_filtered_mode(self, tmp_path: Path) -> None:
        """Test executor with filtered build mode."""
        fo4_path = tmp_path / "Fallout4"
        fo4_path.mkdir()
        (fo4_path / "Data").mkdir()

        executor = BuildStepExecutor("TestMod.esp", fo4_path, BuildMode.FILTERED)

        assert executor.build_mode == BuildMode.FILTERED
