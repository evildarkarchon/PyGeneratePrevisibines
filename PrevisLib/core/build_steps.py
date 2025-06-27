"""Individual build step implementations with detailed logic."""

import shutil
from pathlib import Path
from typing import Any

from loguru import logger

from PrevisLib.models.data_classes import BuildMode
from PrevisLib.utils import file_system as fs


class BuildStepExecutor:
    """Handles detailed execution logic for individual build steps."""

    def __init__(self, plugin_name: str, fo4_path: Path, build_mode: BuildMode) -> None:
        self.plugin_name = plugin_name
        self.plugin_base = self._get_plugin_base_name(plugin_name)
        self.fo4_path = fo4_path
        self.data_path = fo4_path / "Data"
        self.build_mode = build_mode

    def _get_plugin_base_name(self, plugin_name: str) -> str:
        """Extract base name from plugin, validating extension.

        Args:
            plugin_name: Full plugin name with extension

        Returns:
            Base name without extension

        Raises:
            ValueError: If plugin has invalid extension
        """
        valid_extensions: set[str] = {".esp", ".esm", ".esl"}

        # Check if plugin has a valid extension
        plugin_path: Path = Path(plugin_name)
        extension: str = plugin_path.suffix.lower()

        if extension not in valid_extensions:
            raise ValueError(f"Invalid plugin extension '{extension}'. Must be one of: {', '.join(valid_extensions)}")

        return plugin_path.stem

    def validate_precombined_output(self, output_path: Path) -> dict[str, Any]:
        """Validate precombined mesh generation output.

        Args:
            output_path: Path containing generated meshes

        Returns:
            Validation results dictionary
        """
        results: dict[str, Any] = {"valid": True, "mesh_count": 0, "total_size": 0, "errors": []}

        # Count mesh files
        mesh_files: list[Path] = fs.find_files(output_path, "*.nif", recursive=True)
        results["mesh_count"] = len(mesh_files)

        if results["mesh_count"] == 0:
            results["valid"] = False
            results["errors"].append("No mesh files generated")
            return results

        # Calculate total size
        for mesh_file in mesh_files:
            results["total_size"] += mesh_file.stat().st_size

        # Check for minimum reasonable size (1KB per mesh)
        if results["total_size"] < results["mesh_count"] * 1024:
            results["valid"] = False
            results["errors"].append("Generated meshes are suspiciously small")

        # Check for specific error patterns in file names
        for mesh_file in mesh_files:
            if "error" in mesh_file.name.lower():
                results["errors"].append(f"Error mesh found: {mesh_file.name}")

        logger.info(f"Precombined validation: {results['mesh_count']} meshes, {results['total_size'] / (1024 * 1024):.1f} MB total")

        return results

    def prepare_for_archiving(self, source_path: Path) -> bool:
        """Prepare files for archiving by organizing structure.

        Args:
            source_path: Path containing files to archive

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure proper directory structure for BA2
            # Meshes should be in meshes/precombined/[plugin]/ structure
            expected_structure: Path = source_path / "meshes" / "precombined" / self.plugin_base

            if not expected_structure.exists():
                # Reorganize if needed
                nif_files: list[Path] = fs.find_files(source_path, "*.nif", recursive=True)
                if nif_files:
                    fs.ensure_directory(expected_structure)

                    for nif_file in nif_files:
                        # Move to proper location
                        dest: Path = expected_structure / nif_file.name
                        shutil.move(str(nif_file), str(dest))

                    logger.info(f"Reorganized {len(nif_files)} files for archiving")

        except (OSError, shutil.Error) as e:
            logger.error(f"Failed to prepare files for archiving: {e}")
            return False

        else:
            return True

    def validate_visibility_output(self, output_path: Path) -> dict[str, Any]:
        """Validate visibility data generation output.

        Args:
            output_path: Path containing generated visibility data

        Returns:
            Validation results dictionary
        """
        results: dict[str, Any] = {"valid": True, "uvd_count": 0, "total_size": 0, "errors": []}

        # Count UVD files
        uvd_files: list[Path] = fs.find_files(output_path, "*.uvd", recursive=True)
        results["uvd_count"] = len(uvd_files)

        if results["uvd_count"] == 0:
            results["valid"] = False
            results["errors"].append("No visibility data files generated")
            return results

        # Calculate total size
        for uvd_file in uvd_files:
            results["total_size"] += uvd_file.stat().st_size

        # Check for minimum reasonable size
        if results["total_size"] < results["uvd_count"] * 100:
            results["valid"] = False
            results["errors"].append("Generated visibility files are suspiciously small")

        logger.info(f"Visibility validation: {results['uvd_count']} files, {results['total_size'] / 1024:.1f} KB total")

        return results

    def check_plugin_compatibility(self) -> list[str]:
        """Check for potential plugin compatibility issues.

        Returns:
            List of warnings/issues found
        """
        warnings: list[str] = []

        plugin_path: Path = self.data_path / self.plugin_name
        if not plugin_path.exists():
            warnings.append(f"Plugin file not found: {self.plugin_name}")
            return warnings

        # Check file size (very large plugins might have issues)
        size_mb: float = plugin_path.stat().st_size / (1024 * 1024)
        if size_mb > 100:
            warnings.append(f"Plugin is very large ({size_mb:.1f} MB), may cause CK issues")

        # Check for other previs files that might conflict
        existing_main: Path = self.data_path / f"{self.plugin_base} - Main.ba2"
        existing_csg: Path = self.data_path / f"{self.plugin_base} - Geometry.csg"
        existing_cdx: Path = self.data_path / f"{self.plugin_base}.cdx"

        if existing_main.exists():
            warnings.append("Existing Main.ba2 found - will be overwritten")
        if existing_csg.exists():
            warnings.append("Existing Geometry.csg found - will be overwritten")
        if existing_cdx.exists():
            warnings.append("Existing .cdx file found - will be overwritten")

        return warnings


    def create_backup(self, file_path: Path) -> Path | None:
        """Create a backup of a file before modification.

        Args:
            file_path: Path to file to backup

        Returns:
            Path to backup file if created, None otherwise
        """
        if not file_path.exists():
            return None

        backup_path: Path = file_path.with_suffix(f"{file_path.suffix}.backup")

        try:
            shutil.copy2(file_path, backup_path)
            logger.info(f"Created backup: {backup_path.name}")
        except (OSError, shutil.Error) as e:
            logger.error(f"Failed to create backup: {e}")
            return None
        else:
            return backup_path

    def restore_backup(self, backup_path: Path) -> bool:
        """Restore a file from backup.

        Args:
            backup_path: Path to backup file

        Returns:
            True if successful, False otherwise
        """
        if not backup_path.exists():
            logger.error(f"Backup file not found: {backup_path}")
            return False

        original_path: Path = backup_path.with_suffix("")  # Remove .backup

        try:
            shutil.copy2(backup_path, original_path)
            logger.info(f"Restored from backup: {original_path.name}")
        except (OSError, shutil.Error) as e:
            logger.error(f"Failed to restore backup: {e}")
            return False
        else:
            return True
