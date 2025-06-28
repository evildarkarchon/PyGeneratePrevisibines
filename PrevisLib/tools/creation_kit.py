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
        """Generate precombined meshes using Creation Kit.

        Args:
            data_path: Path to Fallout 4 Data directory

        Returns:
            True if successful, False otherwise
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
        """Compress PSG files using Creation Kit.

        Args:
            data_path: Path to Fallout 4 Data directory

        Returns:
            True if successful, False otherwise
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
        """Build CDX files using Creation Kit.

        Args:
            data_path: Path to Fallout 4 Data directory

        Returns:
            True if successful, False otherwise
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
        """Generate visibility data using Creation Kit.

        Args:
            data_path: Path to Fallout 4 Data directory

        Returns:
            True if successful, False otherwise
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
        """Disable graphics DLLs by renaming them to prevent CK graphics issues.

        This matches the batch file behavior of renaming DLLs to .dll-PJMdisabled
        to prevent Creation Kit graphics problems.
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
        """Restore graphics DLLs by renaming them back from .dll-PJMdisabled.

        This matches the batch file behavior of restoring DLLs after CK operations.
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
        """Check Creation Kit log files for errors.

        Args:
            data_path: Path to Fallout 4 Data directory

        Returns:
            True if errors found, False otherwise
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
        """Check if previs generation completed successfully.

        Args:
            data_path: Path to Fallout 4 Data directory

        Returns:
            True if completed successfully, False otherwise
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
