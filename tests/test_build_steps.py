"""Tests for BuildStepExecutor and build step logic."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from PrevisLib.core.build_steps import BuildStepExecutor
from PrevisLib.models.data_classes import BuildMode


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

    @patch("PrevisLib.core.build_steps.fs")
    def test_validate_precombined_output_small_files(self, mock_fs: MagicMock, executor: BuildStepExecutor, tmp_path: Path) -> None:
        """Test precombined output validation with suspiciously small files."""
        output_path = tmp_path / "output"
        output_path.mkdir()

        # Create very small mesh files
        mesh_files = [output_path / "mesh1.nif", output_path / "mesh2.nif"]

        for mesh_file in mesh_files:
            mesh_file.write_text("x")  # Very small file

        mock_fs.find_files.return_value = mesh_files

        with patch("PrevisLib.core.build_steps.logger"):
            result = executor.validate_precombined_output(output_path)

        assert result["valid"] is False
        assert "suspiciously small" in result["errors"][0]

    @patch("PrevisLib.core.build_steps.fs")
    def test_validate_precombined_output_error_mesh(self, mock_fs: MagicMock, executor: BuildStepExecutor, tmp_path: Path) -> None:
        """Test precombined output validation with error mesh files."""
        output_path = tmp_path / "output"
        output_path.mkdir()

        # Create mesh files including one with "error" in name
        mesh_files = [output_path / "mesh1.nif", output_path / "error_mesh.nif"]

        for mesh_file in mesh_files:
            mesh_file.write_text("fake mesh data" * 100)

        mock_fs.find_files.return_value = mesh_files

        with patch("PrevisLib.core.build_steps.logger"):
            result = executor.validate_precombined_output(output_path)

        assert len(result["errors"]) > 0
        assert any("Error mesh found" in error for error in result["errors"])

    @patch("PrevisLib.core.build_steps.fs")
    @patch("PrevisLib.core.build_steps.shutil")
    def test_prepare_for_archiving_reorganize_needed(
        self, mock_shutil: MagicMock, mock_fs: MagicMock, executor: BuildStepExecutor, tmp_path: Path
    ) -> None:
        """Test file preparation when reorganization is needed."""
        source_path = tmp_path / "source"
        source_path.mkdir()

        # Create fake mesh files in wrong location
        mesh_files = [source_path / "mesh1.nif", source_path / "mesh2.nif"]

        for mesh_file in mesh_files:
            mesh_file.write_text("fake mesh")

        mock_fs.find_files.return_value = mesh_files
        mock_fs.ensure_directory = Mock()
        mock_shutil.move = Mock()

        with patch("PrevisLib.core.build_steps.logger"):
            result = executor.prepare_for_archiving(source_path)

        assert result is True
        mock_fs.ensure_directory.assert_called_once()
        assert mock_shutil.move.call_count == 2

    @patch("PrevisLib.core.build_steps.fs")
    def test_prepare_for_archiving_already_organized(self, mock_fs: MagicMock, executor: BuildStepExecutor, tmp_path: Path) -> None:  # noqa: ARG002
        """Test file preparation when files are already organized."""
        source_path = tmp_path / "source"
        expected_structure = source_path / "meshes" / "precombined" / "TestMod"
        expected_structure.mkdir(parents=True)

        result = executor.prepare_for_archiving(source_path)

        assert result is True

    @patch("PrevisLib.core.build_steps.fs")
    @patch("PrevisLib.core.build_steps.shutil")
    def test_prepare_for_archiving_error(
        self,
        mock_shutil: MagicMock,  # noqa: ARG002
        mock_fs: MagicMock,
        executor: BuildStepExecutor,
        tmp_path: Path,
    ) -> None:
        """Test file preparation when error occurs."""
        source_path = tmp_path / "source"
        source_path.mkdir()

        mock_fs.find_files.return_value = [source_path / "mesh1.nif"]
        mock_fs.ensure_directory.side_effect = OSError("Permission denied")

        with patch("PrevisLib.core.build_steps.logger"):
            result = executor.prepare_for_archiving(source_path)

        assert result is False

    @patch("PrevisLib.core.build_steps.fs")
    def test_validate_visibility_output_success(self, mock_fs: MagicMock, executor: BuildStepExecutor, tmp_path: Path) -> None:
        """Test successful visibility output validation."""
        output_path = tmp_path / "output"
        output_path.mkdir()

        # Create fake UVD files
        uvd_files = [output_path / "vis1.uvd", output_path / "vis2.uvd"]

        for uvd_file in uvd_files:
            uvd_file.write_text("visibility data" * 20)

        mock_fs.find_files.return_value = uvd_files

        with patch("PrevisLib.core.build_steps.logger"):
            result = executor.validate_visibility_output(output_path)

        assert result["valid"] is True
        assert result["uvd_count"] == 2
        assert result["total_size"] > 0
        assert result["errors"] == []

    @patch("PrevisLib.core.build_steps.fs")
    def test_validate_visibility_output_no_files(self, mock_fs: MagicMock, executor: BuildStepExecutor, tmp_path: Path) -> None:
        """Test visibility output validation with no files."""
        output_path = tmp_path / "output"
        output_path.mkdir()

        mock_fs.find_files.return_value = []

        result = executor.validate_visibility_output(output_path)

        assert result["valid"] is False
        assert result["uvd_count"] == 0
        assert "No visibility data files generated" in result["errors"]

    @patch("PrevisLib.core.build_steps.fs")
    def test_validate_visibility_output_small_files(self, mock_fs: MagicMock, executor: BuildStepExecutor, tmp_path: Path) -> None:
        """Test visibility output validation with small files."""
        output_path = tmp_path / "output"
        output_path.mkdir()

        # Create very small UVD files
        uvd_files = [output_path / "vis1.uvd"]
        uvd_files[0].write_text("x")  # Very small file

        mock_fs.find_files.return_value = uvd_files

        with patch("PrevisLib.core.build_steps.logger"):
            result = executor.validate_visibility_output(output_path)

        assert result["valid"] is False
        assert "suspiciously small" in result["errors"][0]

    @patch("PrevisLib.core.build_steps.shutil")
    def test_create_backup_success(self, mock_shutil: MagicMock, executor: BuildStepExecutor, tmp_path: Path) -> None:
        """Test successful backup creation."""
        file_path = tmp_path / "test.esp"
        file_path.write_text("plugin content")

        mock_shutil.copy2 = Mock()

        with patch("PrevisLib.core.build_steps.logger"):
            result = executor.create_backup(file_path)

        expected_backup = file_path.with_suffix(".esp.backup")
        assert result == expected_backup
        mock_shutil.copy2.assert_called_once_with(file_path, expected_backup)

    def test_create_backup_nonexistent_file(self, executor: BuildStepExecutor, tmp_path: Path) -> None:
        """Test backup creation for nonexistent file."""
        file_path = tmp_path / "nonexistent.esp"

        result = executor.create_backup(file_path)

        assert result is None

    @patch("PrevisLib.core.build_steps.shutil")
    def test_create_backup_error(self, mock_shutil: MagicMock, executor: BuildStepExecutor, tmp_path: Path) -> None:
        """Test backup creation when error occurs."""
        file_path = tmp_path / "test.esp"
        file_path.write_text("plugin content")

        mock_shutil.copy2.side_effect = OSError("Permission denied")

        with patch("PrevisLib.core.build_steps.logger"):
            result = executor.create_backup(file_path)

        assert result is None

    @patch("PrevisLib.core.build_steps.shutil")
    def test_restore_backup_success(self, mock_shutil: MagicMock, executor: BuildStepExecutor, tmp_path: Path) -> None:
        """Test successful backup restoration."""
        backup_path = tmp_path / "test.esp.backup"
        backup_path.write_text("backup content")

        mock_shutil.copy2 = Mock()

        with patch("PrevisLib.core.build_steps.logger"):
            result = executor.restore_backup(backup_path)

        assert result is True
        original_path = backup_path.with_suffix("")
        mock_shutil.copy2.assert_called_once_with(backup_path, original_path)

    def test_restore_backup_nonexistent(self, executor: BuildStepExecutor, tmp_path: Path) -> None:
        """Test backup restoration for nonexistent backup."""
        backup_path = tmp_path / "nonexistent.backup"

        with patch("PrevisLib.core.build_steps.logger"):
            result = executor.restore_backup(backup_path)

        assert result is False

    @patch("PrevisLib.core.build_steps.shutil")
    def test_restore_backup_error(self, mock_shutil: MagicMock, executor: BuildStepExecutor, tmp_path: Path) -> None:
        """Test backup restoration when error occurs."""
        backup_path = tmp_path / "test.esp.backup"
        backup_path.write_text("backup content")

        mock_shutil.copy2.side_effect = OSError("Permission denied")

        with patch("PrevisLib.core.build_steps.logger"):
            result = executor.restore_backup(backup_path)

        assert result is False


class TestBuildStepExecutorBuildModes:
    """Test BuildStepExecutor with different build modes."""

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

    def test_xbox_mode(self, tmp_path: Path) -> None:
        """Test executor with xbox build mode."""
        fo4_path = tmp_path / "Fallout4"
        fo4_path.mkdir()
        (fo4_path / "Data").mkdir()

        executor = BuildStepExecutor("TestMod.esp", fo4_path, BuildMode.XBOX)

        assert executor.build_mode == BuildMode.XBOX
