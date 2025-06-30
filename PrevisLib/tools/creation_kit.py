"""Creation Kit wrapper for previs generation."""

from pathlib import Path

from loguru import logger

from PrevisLib.models.data_classes import BuildMode, CKPEConfig
from PrevisLib.utils.process import ProcessRunner


class CreationKitWrapper:
    """Wrapper for Creation Kit operations."""

    def __init__(self, ck_path: Path, plugin_name: str, build_mode: BuildMode, ckpe_config: CKPEConfig | None = None) -> None:
        self.ck_path = ck_path
        self.plugin_name = plugin_name
        self.build_mode = build_mode
        self.ckpe_config = ckpe_config
        self.process_runner = ProcessRunner()
        self.ck_directory = ck_path.parent
        # Graphics DLLs that need to be disabled during CK operations
        self.graphics_dlls = ["d3d11.dll", "d3d10.dll", "d3d9.dll", "dxgi.dll", "enbimgui.dll", "d3dcompiler_46e.dll"]

    def generate_precombined(self, data_path: Path) -> bool:
        """
        Generates precombined meshes using the Creation Kit (CK) for the specified data
        path. The function disables graphics DLLs temporarily to ensure compatibility
        with CK, constructs appropriate command-line arguments based on the build mode,
        and executes the CK process. Upon completion, it restores the graphics DLLs and
        logs the result of the operation.

        :param data_path: Path to the directory containing the data required for the
            precombined mesh generation.
        :type data_path: Path
        :return: True if precombined meshes are generated successfully, False otherwise.
        :rtype: bool
        """
        logger.info("Starting precombined mesh generation")

        # Disable graphics DLLs before running CK
        self._disable_graphics_dlls()

        try:
            args: list[str] = [str(self.ck_path), f"-GeneratePrecombined:{self.plugin_name}"]

            if self.build_mode == BuildMode.CLEAN:
                args.extend(["clean", "all"])
            else:
                args.extend(["filtered", "all"])

            success: bool = self.process_runner.execute(
                args,
                timeout=172800,  # 2 Days for CK operations
                show_output=True,
            )

            if success:
                # Check for common CK errors in log
                if self._check_ck_errors(data_path):
                    logger.error("Creation Kit reported errors during precombined generation")
                    return False
                logger.success("Precombined mesh generation completed successfully")
            else:
                logger.error("Creation Kit precombined generation failed")

            return success
        finally:
            # Always restore graphics DLLs, even if operation failed
            self._restore_graphics_dlls()

    def compress_psg(self, data_path: Path) -> bool:
        """
        Compresses a PSG file using the Creation Kit (CK) tool.

        This method invokes the Creation Kit with specific arguments to perform PSG
        file compression for a given plugin. The process includes disabling graphics
        DLLs before the operation and ensures they are restored afterward. If the
        compression succeeds, it additionally checks for errors reported by the CK.
        The method logs progress, success, and error events during the operation.

        :param data_path: The file system path to the PSG data for processing.
        :type data_path: Path
        :return: True if the compression succeeds without errors; otherwise, False.
        :rtype: bool
        """
        logger.info("Starting PSG file compression")

        # Disable graphics DLLs before running CK
        self._disable_graphics_dlls()

        try:
            args: list[str] = [str(self.ck_path), f"-CompressPSG:{self.plugin_name}"]

            success: bool = self.process_runner.execute(
                args,
                timeout=600,  # 10 minutes for PSG compression
                show_output=True,
            )

            if success:
                if self._check_ck_errors(data_path):
                    logger.error("Creation Kit reported errors during PSG compression")
                    return False
                logger.success("PSG compression completed successfully")
            else:
                logger.error("Creation Kit PSG compression failed")

            return success
        finally:
            # Always restore graphics DLLs, even if operation failed
            self._restore_graphics_dlls()

    def build_cdx(self, data_path: Path) -> bool:
        """
        Generates a CDX file using the Creation Kit (CK) by executing a process with
        specific arguments, managing graphics DLLs, and checking for errors in the process.
        This method wraps the functionality surrounding CDX file generation, including
        error handling and resource cleanup.

        :param data_path: Represents the path where the CDX process will check for errors
            or related working files.
        :type data_path: Path
        :return: True if the CDX building process was successful and no errors were
            reported by the Creation Kit, otherwise False.
        :rtype: bool
        """
        logger.info("Starting CDX file generation")

        # Disable graphics DLLs before running CK
        self._disable_graphics_dlls()

        try:
            args: list[str] = [str(self.ck_path), f"-BuildCDX:{self.plugin_name}"]

            success: bool = self.process_runner.execute(
                args,
                timeout=900,  # 15 minutes for CDX building
                show_output=True,
            )

            if success:
                if self._check_ck_errors(data_path):
                    logger.error("Creation Kit reported errors during CDX building")
                    return False
                logger.success("CDX building completed successfully")
            else:
                logger.error("Creation Kit CDX building failed")

            return success
        finally:
            # Always restore graphics DLLs, even if operation failed
            self._restore_graphics_dlls()

    def generate_previs_data(self, data_path: Path) -> bool:
        """
        Generates precomputed visibility (PreVis) data using the Creation Kit (CK) for the
        specified data path. This process ensures that the scene data is optimized for rendering
        by defining visibility for objects and environments. The method disables specific graphics
        DLLs during the operation and ensures their restoration afterward, even in the case of
        failures. It performs several validation checks, including detecting errors or incomplete
        operations reported by the Creation Kit.

        :param data_path: The path to the data directory for which the PreVis data generation
            will be performed.
        :type data_path: Path
        :return: Returns ``True`` if the PreVis data generation succeeded without errors and
            completed properly. Returns ``False`` if the process failed or errors were detected.
        :rtype: bool
        """
        logger.info("Starting previs data generation")

        # Disable graphics DLLs before running CK
        self._disable_graphics_dlls()

        try:
            args: list[str] = [str(self.ck_path), f"-GeneratePreVisData:{self.plugin_name}", "clean", "all"]

            success: bool = self.process_runner.execute(
                args,
                timeout=172800,  # 2 Days for previs generation
                show_output=True,
            )

            if success:
                if self._check_ck_errors(data_path):
                    logger.error("Creation Kit reported errors during previs generation")
                    return False
                if self._check_previs_completion(data_path):
                    logger.success("Previs data generation completed successfully")
                else:
                    logger.error("Previs generation did not complete properly")
                    return False
            else:
                logger.error("Creation Kit previs generation failed")

            return success
        finally:
            # Always restore graphics DLLs, even if operation failed
            self._restore_graphics_dlls()

    def _disable_graphics_dlls(self) -> None:
        """
        Disables specific graphics DLL files to prevent issues with CK graphics. For each
        DLL in the `graphics_dlls` list, it renames the file by appending `-PJMdisabled`
        to the filename. This prevents specific graphics-related DLLs from being loaded.

        The method checks whether the DLL exists in the specified `ck_directory` and
        ensures that a disabled version of the file does not already exist before attempting
        to rename it. If renaming fails due to operating system errors or file permissions,
        a warning is logged.

        :raises OSError: If an operating system-related error occurs during renaming.
        :raises PermissionError: If file permissions prevent renaming the DLL.

        :return: None
        """
        logger.debug("Disabling graphics DLLs to prevent CK graphics issues")

        for dll_name in self.graphics_dlls:
            dll_path = self.ck_directory / dll_name
            disabled_path = self.ck_directory / f"{dll_name}-PJMdisabled"

            if dll_path.exists() and not disabled_path.exists():
                try:
                    dll_path.rename(disabled_path)
                    logger.debug(f"Disabled {dll_name}")
                except (OSError, PermissionError) as e:
                    logger.warning(f"Could not disable {dll_name}: {e}")

    def _restore_graphics_dlls(self) -> None:
        """
        Restores disabled graphics DLLs in the specified directory by renaming them
        back to their original filenames. This process is intended to re-enable the
        use of graphics libraries that were previously disabled.

        The method iterates through a list of graphics DLL names, checking for
        disabled versions of these files in the directory. If a disabled version
        exists and its original version does not, the file is renamed back to its
        original name. Logs are generated to indicate the success or failure of
        restoration attempts.

        :raises OSError: Raised if there is an error while renaming a disabled file.
        :raises PermissionError: Raised if the proper permissions are lacking to
            execute the renaming operation logged during restoration attempts.
        :return: None
        """
        logger.debug("Restoring graphics DLLs")

        for dll_name in self.graphics_dlls:
            dll_path = self.ck_directory / dll_name
            disabled_path = self.ck_directory / f"{dll_name}-PJMdisabled"

            if disabled_path.exists() and not dll_path.exists():
                try:
                    disabled_path.rename(dll_path)
                    logger.debug(f"Restored {dll_name}")
                except (OSError, PermissionError) as e:
                    logger.warning(f"Could not restore {dll_name}: {e}")

    def _check_ck_errors(self, data_path: Path) -> bool:
        """
        Check for errors in the CKPE log file by scanning its contents for specific error patterns.

        This function evaluates error patterns within the log file specified by the CKPE
        configuration. If the log file is located using a relative path, it resolves the path
        relative to the provided data directory. The log file is read, and specific error patterns
        are searched for in the file's content. If any error patterns are detected, the function
        logs the detection and returns `True`. If no errors are found, it returns `False`.

        :param data_path: The path to the directory containing data. Used to resolve a relative
            log file path if the CKPE configuration specifies one.
        :type data_path: Path
        :return: True if any error pattern is found in the log file; otherwise, False.
        :rtype: bool
        """
        # Skip log checking if no CKPE config or no log file configured
        if not self.ckpe_config or not self.ckpe_config.log_output_file:
            logger.debug("Skipping CK error checking - no log file configured in CKPE")
            return False

        # Enhanced error patterns to match the batch file exactly
        error_patterns: list[str] = [
            "DEFAULT: OUT OF HANDLE ARRAY ENTRIES",  # Exact match from batch file
            "Failed to load",
            "ERROR:",
            "FATAL:",
            "Exception",
        ]

        # Use the configured log file path
        log_path = Path(self.ckpe_config.log_output_file)

        # If it's a relative path, resolve it relative to the data directory
        if not log_path.is_absolute():
            log_path = data_path / log_path

        if log_path.exists():
            try:
                with log_path.open(encoding="utf-8", errors="ignore") as f:
                    content: str = f.read()
                    for pattern in error_patterns:
                        if pattern in content:
                            logger.error(f"Found error pattern '{pattern}' in {log_path}")
                            return True
            except (OSError, UnicodeDecodeError) as e:
                logger.warning(f"Could not read log file {log_path}: {e}")
        else:
            logger.warning(f"Configured CK log file not found: {log_path}")

        return False

    def _check_previs_completion(self, data_path: Path) -> bool:
        """
        Checks the completion status of previs generation based on log file analysis. This method evaluates the content
        of the log file associated with the CKPE configuration for patterns indicating failure. If the log file exists
        and contains any of the predefined failure patterns, the function returns False. If the log file is missing or
        does not contain failure patterns, the function either returns True or logs appropriate warnings.

        :param data_path: The path to the directory containing relevant data files, used as a base path to resolve
            the log file if specified as a relative path.
        :type data_path: Path
        :return: True if no failure patterns are found in the log file or the log file is not configured or does not
            exist, otherwise False.
        :rtype: bool
        """
        # Skip log checking if no CKPE config or no log file configured
        if not self.ckpe_config or not self.ckpe_config.log_output_file:
            logger.debug("Skipping previs completion checking - no log file configured in CKPE")
            return True

        # Enhanced completion failure patterns to match the batch file exactly
        completion_patterns: list[str] = [
            "ERROR: visibility task did not complete.",  # Exact match from batch file
            "Previs generation failed",
            "Could not complete previs",
        ]

        # Use the configured log file path
        log_path = Path(self.ckpe_config.log_output_file)

        # If it's a relative path, resolve it relative to the data directory
        if not log_path.is_absolute():
            log_path = data_path / log_path

        if log_path.exists():
            try:
                with log_path.open(encoding="utf-8", errors="ignore") as f:
                    content: str = f.read()
                    for pattern in completion_patterns:
                        if pattern in content:
                            logger.warning(f"Found completion failure pattern '{pattern}' in {log_path}")
                            return False
            except (OSError, UnicodeDecodeError) as e:
                logger.warning(f"Could not read log file {log_path}: {e}")
        else:
            logger.warning(f"Configured CK log file not found: {log_path}")

        return True
