"""Tests for PrevisBuilder core orchestration."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from PrevisLib.config.settings import Settings
from PrevisLib.core.builder import PrevisBuilder
from PrevisLib.models.data_classes import BuildMode, BuildStep, ToolPaths


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
    @patch("PrevisLib.core.builder.fs")
    def test_step_generate_precombined_success(self, mock_fs: MagicMock, mock_validate_scripts: MagicMock, mock_settings: Settings) -> None:
        """Test successful precombined generation step."""
        mock_validate_scripts.return_value = (True, "Scripts validated")
        builder = PrevisBuilder(mock_settings)
        builder.ck_wrapper = Mock()
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

    @patch("PrevisLib.core.builder.validate_xedit_scripts")
    @patch("PrevisLib.core.builder.fs")
    def test_step_generate_precombined_no_meshes(
        self, mock_fs: MagicMock, mock_validate_scripts: MagicMock, mock_settings: Settings
    ) -> None:
        """Test precombined generation step when no meshes generated."""
        mock_validate_scripts.return_value = (True, "Scripts validated")
        builder = PrevisBuilder(mock_settings)
        builder.ck_wrapper = Mock()
        builder.ck_wrapper.generate_precombined.return_value = True
        builder.output_path = Path("/fake/output")

        mock_fs.count_files.return_value = 0  # No meshes generated

        with patch("PrevisLib.core.builder.logger"):
            result = builder._step_generate_precombined()

        assert result is False

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
