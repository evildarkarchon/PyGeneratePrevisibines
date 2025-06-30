"""Main builder orchestration for previs generation."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from PrevisLib.config.settings import Settings
from PrevisLib.models.data_classes import ArchiveTool, BuildStep, CKPEConfig
from PrevisLib.tools import ArchiveWrapper, CKPEConfigHandler, CreationKitWrapper, XEditWrapper
from PrevisLib.utils import file_system as fs
from PrevisLib.utils.validation import validate_xedit_scripts

if TYPE_CHECKING:
    from collections.abc import Callable


class PrevisBuilder:
    """Main orchestrator for the previs build process."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.plugin_name = settings.plugin_name
        self.build_mode = settings.build_mode
        self.start_time: datetime | None = None
        self.current_step: BuildStep | None = None
        self.completed_steps: list[BuildStep] = []
        self.failed_step: BuildStep | None = None

        # Validate and store plugin base name
        self.plugin_base_name: str = self._get_plugin_base_name()

        # Type annotations for tool wrappers
        self.archive_wrapper: ArchiveWrapper

        # Initialize tool wrappers
        if settings.tool_paths.creation_kit is None:
            raise ValueError("Creation Kit path is required but not configured")
        if settings.tool_paths.xedit is None:
            raise ValueError("xEdit path is required but not configured")

        # Validate xEdit scripts early (like the batch file does)
        script_valid, script_message = validate_xedit_scripts(settings.tool_paths.xedit)
        if not script_valid:
            raise ValueError(f"xEdit script validation failed: {script_message}")

        self.ck_wrapper = CreationKitWrapper(settings.tool_paths.creation_kit, self.plugin_name, self.build_mode, settings.ckpe_config)
        self.xedit_wrapper = XEditWrapper(settings.tool_paths.xedit, self.plugin_name)

        # Validate required paths
        if settings.tool_paths.fallout4 is None:
            raise ValueError("Fallout 4 path is required but not configured")

        # Choose archive tool
        if settings.archive_tool == ArchiveTool.BSARCH:
            if settings.tool_paths.bsarch is None:
                raise ValueError("BSArch path is required but not configured")
            self.archive_wrapper = ArchiveWrapper(ArchiveTool.BSARCH, settings.tool_paths.bsarch, self.build_mode)
        else:
            if settings.tool_paths.archive2 is None:
                raise ValueError("Archive2 path is required but not configured")
            self.archive_wrapper = ArchiveWrapper(ArchiveTool.ARCHIVE2, settings.tool_paths.archive2, self.build_mode)

        # CKPE config handler
        self.ckpe_handler = CKPEConfigHandler(settings.tool_paths.fallout4)

        # Paths
        self.fo4_path = settings.tool_paths.fallout4
        self.data_path = self.fo4_path / "Data"
        self.output_path = self.data_path / "PreCombined"
        self.temp_path = self.data_path / "Temp"

    def _get_plugin_base_name(self) -> str:
        """
        Extracts and returns the base name of a plugin, excluding its file extension. The method
        validates that the extension is among the permitted types (".esp", ".esm", ".esl"). If the
        plugin's extension does not match any of these, it raises a ValueError. The base name is
        obtained using the stem of the file path.

        :param self: Reference to the current instance of the class.
        :return: The base name of the plugin as a string.
        :raises ValueError: If the plugin's extension is not one of the valid extensions.
        """
        valid_extensions: set[str] = {".esp", ".esm", ".esl"}

        # Check if plugin has a valid extension
        plugin_path: Path = Path(self.plugin_name)
        extension: str = plugin_path.suffix.lower()

        if extension not in valid_extensions:
            raise ValueError(f"Invalid plugin extension '{extension}'. Must be one of: {', '.join(valid_extensions)}")

        return plugin_path.stem

    def build(self, start_from_step: BuildStep | None = None) -> bool:
        """
        Executes the build process for the plugin by running a series of predefined steps.
        The method starts by initializing configurations, determining the steps to execute,
        and iterates over them, executing each one. Each step's outcome is logged, and the
        process halts if a step fails. A successful build is logged upon completion.

        :param start_from_step: The build step from which to start execution. If None, execution
            begins from the first step.
        :type start_from_step: BuildStep | None
        :return: True if all steps completed successfully, False if any step failed.
        :rtype: bool
        """
        logger.info(f"Starting previs build for {self.plugin_name}")
        logger.info(f"Build mode: {self.build_mode.value}")
        self.start_time = datetime.now()

        # Load CKPE config if available
        ckpe_config: CKPEConfig | None = self.ckpe_handler.load_config(self.plugin_base_name)
        if ckpe_config:
            self.settings.ckpe_config = ckpe_config
            logger.info("Loaded CKPE configuration")

        # Determine which steps to run
        steps_to_run: list[BuildStep] = self._get_steps_to_run(start_from_step)

        # Execute each step
        for step in steps_to_run:
            self.current_step = step
            logger.info(f"Executing step: {step}")

            try:
                success: bool = self._execute_step(step)

                if success:
                    self.completed_steps.append(step)
                    logger.success(f"Completed step: {step}")
                else:
                    self.failed_step = step
                    logger.error(f"Failed at step: {step}")
                    return False

            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception as e:  # noqa: BLE001
                self.failed_step = step
                logger.error(f"Exception during step {step}: {e}")
                return False

        # Build completed successfully
        elapsed: timedelta = datetime.now() - self.start_time
        logger.success(f"Build completed successfully in {elapsed}")
        return True

    def _get_steps_to_run(self, start_from: BuildStep | None) -> list[BuildStep]:
        """
        Determines and returns the list of build steps to be executed starting from a
        specific step. If no starting step is specified, all steps are returned. If the
        specified starting step is invalid, a warning is logged, and all steps are
        returned.

        :param start_from: The starting build step from which to execute the steps.
            If None, all steps are executed.
        :type start_from: BuildStep | None
        :return: A list of build steps to be executed starting from the specified step.
        :rtype: list[BuildStep]
        """
        all_steps: list[BuildStep] = list(BuildStep)

        if start_from is None:
            return all_steps

        try:
            start_index: int = all_steps.index(start_from)
            return all_steps[start_index:]
        except ValueError:
            logger.warning(f"Invalid start step: {start_from}, running all steps")
            return all_steps

    def _execute_step(self, step: BuildStep) -> bool:
        """
        Executes the function associated with the given build step. Maps a build step
        to its corresponding method and calls the method to execute the step logic.
        If no corresponding method is implemented for the given step, logs an error
        and returns False.

        :param step: The build step to be executed.
        :type step: BuildStep
        :return: True if the execution of the step was successful, otherwise False.
        :rtype: bool
        """
        step_map: dict[BuildStep, Callable[[], bool]] = {
            BuildStep.GENERATE_PRECOMBINED: self._step_generate_precombined,
            BuildStep.MERGE_COMBINED_OBJECTS: self._step_merge_combined_objects,
            BuildStep.ARCHIVE_MESHES: self._step_archive_meshes,
            BuildStep.COMPRESS_PSG: self._step_compress_psg,
            BuildStep.BUILD_CDX: self._step_build_cdx,
            BuildStep.GENERATE_PREVIS: self._step_generate_previs,
            BuildStep.MERGE_PREVIS: self._step_merge_previs,
            BuildStep.FINAL_PACKAGING: self._step_final_packaging,
        }

        step_func: Callable[[], bool] | None = step_map.get(step)
        if step_func:
            return step_func()
        logger.error(f"No implementation for step: {step}")
        return False

    def _step_generate_precombined(self) -> bool:
        """
        Generates precombined meshes using the Creation Kit. This process involves cleaning
        the output directory, running the Creation Kit to generate the meshes, and verifying
        the successful generation of both the mesh files and the CombinedObjects.esp file.

        :raises FileNotFoundError: If CombinedObjects.esp is not created within the specified
            timeout during the verification phase.

        :return: Boolean indicating whether the precombined meshes were successfully
            generated.
        :rtype: bool
        """
        logger.info("Step 1: Generating precombined meshes")

        # Clean output directory
        fs.clean_directory(self.output_path)

        # Run Creation Kit
        success: bool = self.ck_wrapper.generate_precombined(self.data_path)

        if success:
            # Check if files were generated
            mesh_count: int = fs.count_files(self.output_path, "*.nif", recursive=True)
            if mesh_count == 0:
                logger.error("No precombined meshes were generated")
                return False
            logger.info(f"Generated {mesh_count} precombined mesh files")

            # Check for CombinedObjects.esp output file
            combined_objects_path: Path = self.data_path / "CombinedObjects.esp"
            if not fs.wait_for_output_file(combined_objects_path, timeout=60.0, check_interval=1.0):
                logger.error("CombinedObjects.esp was not created by Creation Kit")
                raise FileNotFoundError
            logger.info("CombinedObjects.esp successfully created")

        return success

    def _step_merge_combined_objects(self) -> bool:
        """
        Merges combined objects using the specified xEdit script. This function logs
        progress, locates the necessary script for merging combined objects, and
        executes the merge process through the xEdit wrapper. If the script cannot
        be found, the process is halted, and the failure is logged.

        :return: True if the merge process is successful, False otherwise
        :rtype: bool
        """
        logger.info("Step 2: Merging combined objects")

        # Find the merge script
        script_path: Path | None = self._find_xedit_script("Merge Combined Objects")
        if not script_path:
            logger.error("Could not find Merge Combined Objects script")
            return False

        # Run xEdit merge
        return self.xedit_wrapper.merge_combined_objects(self.data_path, script_path)

    def _step_archive_meshes(self) -> bool:
        """
        Archives precombined meshes into a BA2 archive file and cleans up loose files
        upon successful archiving. This is part of the workflow for managing and packaging
        game asset files.

        :raises RuntimeError: If an error occurs during the archiving process within
            the `archive_wrapper` implementation.

        :rtype: bool
        :return: A boolean indicating whether the archiving process was successful.
        """
        logger.info("Step 3: Archiving precombined meshes")

        archive_path: Path = self.data_path / f"{self.plugin_base_name} - Main.ba2"

        # Create archive from precombined directory
        success: bool = self.archive_wrapper.create_archive(archive_path, self.output_path, compress=True)

        if success:
            # Clean up loose files after archiving
            fs.clean_directory(self.output_path, create=False)
            logger.info(f"Created archive: {archive_path.name}")

        return success

    def _step_compress_psg(self) -> bool:
        """
        Compresses PSG files using the configured CK wrapper.

        This method is part of a multi-step process for handling PSG files. It
        invokes the `compress_psg` function provided by the `ck_wrapper` while
        utilizing the specified `data_path`. Logging is performed to indicate the
        step in progress.

        :return: A boolean indicating whether the compression was successful.
        :rtype: bool
        """
        logger.info("Step 4: Compressing PSG files")

        return self.ck_wrapper.compress_psg(self.data_path)

    def _step_build_cdx(self) -> bool:
        """
        Builds CDX files as part of a specific processing step.

        This method logs the initiation of Step 5, which involves constructing
        CDX files through the `build_cdx` method of the `ck_wrapper` object,
        using the specified `data_path`. The method returns a boolean value
        indicating the success or failure of this operation.

        :return: A boolean value indicating whether the CDX files were
            successfully built.
        :rtype: bool
        """
        logger.info("Step 5: Building CDX files")

        return self.ck_wrapper.build_cdx(self.data_path)

    def _step_generate_previs(self) -> bool:
        """
        Generates visibility data using the Creation Kit and processes the generated data.

        This method orchestrates the process of generating visibility data by cleaning the
        temporary directory, invoking the Creation Kit, and validating the output files.
        It ensures that the visibility data files and the `Previs.esp` file are successfully
        created and cleans up the temporary output directory before processing.

        :raises FileNotFoundError: If `Previs.esp` file is not generated within the timeout period.

        :return: Indicates whether the visibility data generation was successful.
        :rtype: bool
        """
        logger.info("Step 6: Generating visibility data")

        # Clean temp directory for previs output
        fs.clean_directory(self.temp_path)

        # Run Creation Kit
        success: bool = self.ck_wrapper.generate_previs_data(self.data_path)

        if success:
            # Check if files were generated
            vis_count: int = fs.count_files(self.temp_path, "*.uvd", recursive=True)
            if vis_count == 0:
                logger.error("No visibility data files were generated")
                return False
            logger.info(f"Generated {vis_count} visibility data files")

            # Check for Previs.esp output file
            previs_path: Path = self.data_path / "Previs.esp"
            if not fs.wait_for_output_file(previs_path, timeout=120.0, check_interval=2.0):
                logger.error("Previs.esp was not created by Creation Kit")
                raise FileNotFoundError
            logger.info("Previs.esp successfully created")

        return success

    def _step_merge_previs(self) -> bool:
        """
        Merges previs data during step 7 of the process.

        This method locates the appropriate xEdit script for merging previs data,
        logs the process, and attempts to execute the merge using the `xedit_wrapper`.

        :return: True if the merge operation succeeds, False if the script could not
            be found or the merge fails.
        :rtype: bool
        """
        logger.info("Step 7: Merging previs data")

        # Find the merge script
        script_path: Path | None = self._find_xedit_script("Merge Previs")
        if not script_path:
            logger.error("Could not find Merge Previs script")
            return False

        # Run xEdit merge
        return self.xedit_wrapper.merge_previs(self.data_path, script_path)

    def _step_final_packaging(self) -> bool:
        """
        Handles the final packaging step for the plugin. This involves verifying the
        existence of the main archive, optionally adding visibility data to it if
        available, and performing clean-up operations as necessary. The method
        returns a boolean indicating the success or failure of the operation.

        :return: True if the process completes successfully, False otherwise
        :rtype: bool
        """
        logger.info("Step 8: Final packaging")

        main_archive_path: Path = self.data_path / f"{self.plugin_base_name} - Main.ba2"

        # Verify main archive exists first
        if not main_archive_path.exists():
            logger.error(f"Main archive not found: {main_archive_path}")
            return False

        # Add visibility data to existing archive (matches original batch file behavior)
        if self.temp_path.exists() and not fs.is_directory_empty(self.temp_path):
            # Get all files from temp directory to add to archive
            vis_files: list[Path] = list(self.temp_path.rglob("*"))
            vis_files = [f for f in vis_files if f.is_file()]  # Only files, not directories

            if vis_files:
                success: bool = self.archive_wrapper.add_to_archive(main_archive_path, vis_files, self.temp_path)

                if not success:
                    logger.error("Failed to add visibility data to archive")
                    return False

                # Clean up temp directory
                fs.clean_directory(self.temp_path, create=False)
                logger.info("Added visibility data to archive")
            else:
                logger.warning("No visibility files found to add to archive")
        else:
            logger.warning("No visibility files found to add to archive")

        logger.success("All previs files packaged successfully")
        return True

    def _find_xedit_script(self, script_name: str) -> Path | None:
        """
        Finds the xEdit script path based on the given script name.

        This method searches for a script with the given name in multiple common
        locations under the "Edit Scripts" directory. It also checks for different
        file extensions such as `.pas`, `.psc`, and `.txt`. If the script is found, it
        returns the path to the script; otherwise, it returns `None`.

        :param script_name: The name of the script to locate (without extension).
        :type script_name: str
        :return: The path to the script, if it exists; otherwise, `None`.
        :rtype: Path | None
        :raises ValueError: If the xEdit path is not configured in the settings.
        """
        if self.settings.tool_paths.xedit is None:
            raise ValueError("xEdit path is required but not configured")

        # Common script locations
        possible_paths: list[Path] = [
            self.settings.tool_paths.xedit.parent / "Edit Scripts",
            self.data_path / "Edit Scripts",
            self.fo4_path / "Edit Scripts",
        ]

        for base_path in possible_paths:
            if base_path.exists():
                # Try different extensions
                for ext in [".pas", ".psc", ".txt"]:
                    script_path: Path = base_path / f"{script_name}{ext}"
                    if script_path.exists():
                        return script_path

        return None

    def get_resume_options(self) -> list[BuildStep]:
        """
        Provides functionality to retrieve a list of build steps from which the
        process can be resumed. If a step has failed, this method allows resuming
        from the point of failure or any subsequent step. Otherwise, it enables
        starting from any step.

        :returns: A list of build steps from which the process can be resumed.
        :rtype: list[BuildStep]
        """
        if self.failed_step:
            # Can resume from the failed step or any step after
            all_steps: list[BuildStep] = list(BuildStep)
            failed_index: int = all_steps.index(self.failed_step)
            return all_steps[failed_index:]
        # Can start from any step
        return list(BuildStep)

    def cleanup(self) -> bool:
        """
        Cleans up previs files by deleting specific files and cleaning specified
        directories. The files to delete and directories to clean are determined
        by the `data_path`, `plugin_base_name`, `output_path`, and `temp_path`.
        The method ensures safe deletion and logs the status of each operation.

        :param self: Instance of the containing class.
        :return: True if all operations succeed, False if any fail.
        :rtype: bool

        :raises Exception: Logs an error if a file deletion fails due to an unexpected
            exception.
        """
        logger.info("Cleaning up previs files")

        # Files to delete
        files_to_clean: list[Path] = [
            self.data_path / f"{self.plugin_base_name} - Main.ba2",
            self.data_path / f"{self.plugin_base_name} - Geometry.csg",  # Only exists in clean mode
            self.data_path / f"{self.plugin_base_name}.cdx",  # Only exists in clean mode
            self.data_path / "CombinedObjects.esp",
            self.data_path / "Previs.esp",
        ]

        # Directories to clean
        dirs_to_clean: list[Path] = [self.output_path, self.temp_path]

        success: bool = True

        # Delete files
        for file_path in files_to_clean:
            if file_path.exists():
                try:
                    if not fs.safe_delete(file_path):
                        logger.error(f"Failed to delete: {file_path.name}")
                        success = False
                except Exception as e:
                    logger.error(f"Failed to delete {file_path.name}: {e}")
                    success = False

        # Clean directories
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                fs.clean_directory(dir_path, create=False)
                logger.info(f"Cleaned directory: {dir_path.name}")

        return success

    def cleanup_working_files(self) -> bool:
        """
        Cleans up the working files generated during previous operations.

        The method attempts to delete a predefined list of working files from the file
        system. It iterates through the list of file paths and tries to remove each
        file. If a file cannot be deleted, an error is logged, and the overall success
        flag is updated to indicate failure.

        :return: A boolean indicating whether all files were successfully deleted.
        :rtype: bool
        """
        logger.info("Cleaning up working files")

        # Working files to delete (from original batch file :Cleanup section)
        working_files: list[Path] = [
            self.data_path / "CombinedObjects.esp",
            self.data_path / "Previs.esp",
        ]

        success: bool = True

        # Delete working files
        for file_path in working_files:
            if file_path.exists():
                if fs.safe_delete(file_path):
                    logger.info(f"Deleted working file: {file_path.name}")
                else:
                    logger.error(f"Failed to delete working file: {file_path.name}")
                    success = False

        return success
