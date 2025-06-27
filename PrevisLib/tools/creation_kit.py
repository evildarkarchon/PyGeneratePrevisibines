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
        # File system operations will use module functions directly

    def generate_precombined(self, data_path: Path) -> bool:
        """Generate precombined meshes using Creation Kit.

        Args:
            data_path: Path to Fallout 4 Data directory

        Returns:
            True if successful, False otherwise
        """
        logger.info("Starting precombined mesh generation")

        args: list[str] = [str(self.ck_path), f"-GeneratePrecombined:{self.plugin_name}"]

        if self.build_mode == BuildMode.CLEAN:
            args.extend(["clean", "all"])
        else:
            args.extend(["filtered", "all"])

        success: bool = self.process_runner.run_process(
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

    def compress_psg(self, data_path: Path) -> bool:
        """Compress PSG files using Creation Kit.

        Args:
            data_path: Path to Fallout 4 Data directory

        Returns:
            True if successful, False otherwise
        """
        logger.info("Starting PSG file compression")

        args: list[str] = [str(self.ck_path), f"-CompressPSG:{self.plugin_name}"]

        success: bool = self.process_runner.run_process(
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

    def build_cdx(self, data_path: Path) -> bool:
        """Build CDX files using Creation Kit.

        Args:
            data_path: Path to Fallout 4 Data directory

        Returns:
            True if successful, False otherwise
        """
        logger.info("Starting CDX file generation")

        args: list[str] = [str(self.ck_path), f"-BuildCDX:{self.plugin_name}"]

        success: bool = self.process_runner.run_process(
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

    def generate_previs_data(self, data_path: Path) -> bool:
        """Generate visibility data using Creation Kit.

        Args:
            data_path: Path to Fallout 4 Data directory

        Returns:
            True if successful, False otherwise
        """
        logger.info("Starting previs data generation")

        args: list[str] = [str(self.ck_path), f"-GeneratePreVisData:{self.plugin_name}", "clean", "all"]

        success: bool = self.process_runner.run_process(
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

        log_patterns: list[str] = ["OUT OF HANDLE ARRAY ENTRIES", "Failed to load", "ERROR:", "FATAL:", "Exception"]

        # Use the configured log file path
        log_path = Path(self.ckpe_config.log_output_file)

        # If it's a relative path, resolve it relative to the data directory
        if not log_path.is_absolute():
            log_path = data_path / log_path

        if log_path.exists():
            try:
                with log_path.open(encoding="utf-8", errors="ignore") as f:
                    content: str = f.read()
                    for pattern in log_patterns:
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

        # Look for completion indicators in logs
        completion_patterns: list[str] = ["visibility task did not complete", "Previs generation failed", "Could not complete previs"]

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
                            logger.error(f"Found completion failure pattern '{pattern}' in {log_path}")
                            return False
            except (OSError, UnicodeDecodeError) as e:
                logger.warning(f"Could not read log file {log_path}: {e}")
        else:
            logger.warning(f"Configured CK log file not found: {log_path}")

        return True
