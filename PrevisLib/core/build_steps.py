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

    @staticmethod
    def _get_plugin_base_name(plugin_name: str) -> str:
        """
        Gets the base name of a plugin file by removing its extension. It ensures the plugin has
        a valid extension from the set of `.esp`, `.esm`, or `.esl`. Raises a `ValueError` if
        the plugin does not have a valid extension.

        :param plugin_name: The full name of the plugin file, including its extension.
        :type plugin_name: str
        :raises ValueError: If the plugin extension is not one of `.esp`, `.esm`, or `.esl`.
        :return: The base name of the plugin file without its extension.
        :rtype: str
        """
        valid_extensions: set[str] = {".esp", ".esm", ".esl"}

        # Check if plugin has a valid extension
        plugin_path: Path = Path(plugin_name)
        extension: str = plugin_path.suffix.lower()

        if extension not in valid_extensions:
            raise ValueError(f"Invalid plugin extension '{extension}'. Must be one of: {', '.join(valid_extensions)}")

        return plugin_path.stem

    @staticmethod
    def validate_precombined_output(output_path: Path) -> dict[str, Any]:
        """
        Validates the output of precombined meshes by checking for the presence of files,
        their total size, and potential error patterns in the file names.

        :param output_path: Path to the directory containing the precombined outputs
        :type output_path: Path
        :return: A dictionary containing validation results, including whether the validation
            was successful, the count of mesh files, the total size of the files, and any errors found
        :rtype: dict[str, Any]
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
        """
        Ensures that the source directory has the proper structure required for archiving,
        specifically for BA2 format. Mesh files are reorganized into the appropriate
        directory structure under "meshes/precombined/[plugin_base]". If necessary,
        it moves `.nif` files to the expected location and logs the number of files
        processed. Returns `True` if the operation completes successfully, otherwise
        logs an error and returns `False`.

        :param source_path: Path to the source directory containing mesh files
        :type source_path: Path
        :return: Indicates whether the preparation for archiving was successful
        :rtype: bool
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

        except (OSError, Exception) as e:
            logger.error(f"Failed to prepare files for archiving: {e}")
            return False

        else:
            return True

    @staticmethod
    def validate_visibility_output(output_path: Path) -> dict[str, Any]:
        """
        Validates the visibility output by analyzing the files in the given directory.
        The function checks for the presence of UVD files, calculates their total size,
        and reports if their size is suspiciously small. Results include whether the output
        is valid, the count of UVD files, the total size of these files, and any errors encountered.

        :param output_path: Directory path where visibility output files are stored.
        :type output_path: Path
        :return: A dictionary containing the validation results with the following keys:
                 - "valid" (bool): Whether the visibility output is considered valid.
                 - "uvd_count" (int): The number of UVD files found.
                 - "total_size" (int): The total size of all UVD files in bytes.
                 - "errors" (list): A list of error messages if the output is invalid.
        :rtype: dict[str, Any]
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
        """
        Checks the compatibility of a specific plugin file with the system by performing various
        validations. Verifies the existence of the plugin file, checks its size to detect potential
        issues with unusually large files, and examines if certain related files that may conflict
        or be overwritten by this plugin already exist in the target directory.

        :param self: The instance of the class calling this method.
        :return: A list of warning messages indicating potential compatibility or conflict issues
            with the plugin.
        :rtype: list[str]
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

    @staticmethod
    def create_backup(file_path: Path) -> Path | None:
        """
        Create a backup file by copying the specified file and appending a
        `.backup` suffix to its name. If the specified file does not exist,
        return None. Logs information about the backup creation process or
        errors encountered.

        :param file_path: The path to the file to back up.

        :return: The path to the created backup file if successful,
                 otherwise None.
        """
        if not file_path.exists():
            return None

        backup_path: Path = file_path.with_suffix(f"{file_path.suffix}.backup")

        try:
            shutil.copy2(file_path, backup_path)
            logger.info(f"Created backup: {backup_path.name}")
        except (OSError, Exception) as e:
            logger.error(f"Failed to create backup: {e}")
            return None
        else:
            return backup_path

    @staticmethod
    def restore_backup(backup_path: Path) -> bool:
        """
        Restores a file from its backup. This method attempts to locate the backup file
        specified by the path provided and restore the original file by copying the backup
        to the original location. If the process is successful, the original file will be
        restored from the backup. If the backup file does not exist, or if there is any
        failure during the restoration process, the method will return a failure status.

        :param backup_path: The path to the backup file that needs to be restored.
        :type backup_path: Path
        :return: A boolean indicating whether the restoration process was successful.
        :rtype: bool
        """
        if not backup_path.exists():
            logger.error(f"Backup file not found: {backup_path}")
            return False

        original_path: Path = backup_path.with_suffix("")  # Remove .backup

        try:
            shutil.copy2(backup_path, original_path)
            logger.info(f"Restored from backup: {original_path.name}")
        except (OSError, Exception) as e:
            logger.error(f"Failed to restore backup: {e}")
            return False
        else:
            return True
