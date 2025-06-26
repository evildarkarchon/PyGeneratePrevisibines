"""Creation Kit wrapper for previs generation."""

from pathlib import Path

from loguru import logger

from ..models.data_classes import BuildMode
from ..utils.process import ProcessRunner


class CreationKitWrapper:
    """Wrapper for Creation Kit operations."""
    
    def __init__(self, ck_path: Path, plugin_name: str, build_mode: BuildMode):
        self.ck_path = ck_path
        self.plugin_name = plugin_name
        self.build_mode = build_mode
        self.process_runner = ProcessRunner()
        # File system operations will use module functions directly
        
    def generate_precombined(self, data_path: Path, output_path: Path) -> bool:
        """Generate precombined meshes using Creation Kit.
        
        Args:
            data_path: Path to Fallout 4 Data directory
            output_path: Path for output files
            
        Returns:
            True if successful, False otherwise
        """
        logger.info("Starting precombined mesh generation")
        
        args = [
            str(self.ck_path),
            f"-GeneratePrecombined:{self.plugin_name}",
            f"-DataPath:{data_path}",
            f"-OutputPath:{output_path}"
        ]
        
        if self.build_mode == BuildMode.FILTERED:
            args.append("-FilteredOnly:1")
        elif self.build_mode == BuildMode.XBOX:
            args.append("-XboxOne:1")
            
        success = self.process_runner.run_process(
            args, 
            timeout=1800,  # 30 minutes for CK operations
            show_output=True
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
        
        args = [
            str(self.ck_path),
            f"-CompressPSG:{self.plugin_name}",
            f"-DataPath:{data_path}"
        ]
        
        success = self.process_runner.run_process(
            args,
            timeout=600,  # 10 minutes for PSG compression
            show_output=True
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
        
        args = [
            str(self.ck_path),
            f"-BuildCDX:{self.plugin_name}",
            f"-DataPath:{data_path}"
        ]
        
        success = self.process_runner.run_process(
            args,
            timeout=900,  # 15 minutes for CDX building
            show_output=True
        )
        
        if success:
            if self._check_ck_errors(data_path):
                logger.error("Creation Kit reported errors during CDX building")
                return False
            logger.success("CDX building completed successfully")
        else:
            logger.error("Creation Kit CDX building failed")
            
        return success
        
    def generate_previs_data(self, data_path: Path, output_path: Path) -> bool:
        """Generate visibility data using Creation Kit.
        
        Args:
            data_path: Path to Fallout 4 Data directory
            output_path: Path for output files
            
        Returns:
            True if successful, False otherwise
        """
        logger.info("Starting previs data generation")
        
        args = [
            str(self.ck_path),
            f"-GeneratePrevis:{self.plugin_name}",
            f"-DataPath:{data_path}",
            f"-OutputPath:{output_path}"
        ]
        
        if self.build_mode == BuildMode.FILTERED:
            args.append("-FilteredOnly:1")
        elif self.build_mode == BuildMode.XBOX:
            args.append("-XboxOne:1")
            
        success = self.process_runner.run_process(
            args,
            timeout=2400,  # 40 minutes for previs generation
            show_output=True
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
        log_patterns = [
            "OUT OF HANDLE ARRAY ENTRIES",
            "Failed to load",
            "ERROR:",
            "FATAL:",
            "Exception"
        ]
        
        # Check common CK log locations
        possible_log_paths = [
            data_path.parent / "Logs" / "CreationKit.log",
            Path.home() / "Documents" / "My Games" / "Fallout4" / "Logs" / "CreationKit.log",
            data_path / "Logs" / "CreationKit.log"
        ]
        
        for log_path in possible_log_paths:
            if log_path.exists():
                try:
                    with open(log_path, encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        for pattern in log_patterns:
                            if pattern in content:
                                logger.error(f"Found error pattern '{pattern}' in {log_path}")
                                return True
                except Exception as e:
                    logger.warning(f"Could not read log file {log_path}: {e}")
                    
        return False
        
    def _check_previs_completion(self, data_path: Path) -> bool:
        """Check if previs generation completed successfully.
        
        Args:
            data_path: Path to Fallout 4 Data directory
            
        Returns:
            True if completed successfully, False otherwise
        """
        # Look for completion indicators in logs
        completion_patterns = [
            "visibility task did not complete",
            "Previs generation failed",
            "Could not complete previs"
        ]
        
        possible_log_paths = [
            data_path.parent / "Logs" / "CreationKit.log",
            Path.home() / "Documents" / "My Games" / "Fallout4" / "Logs" / "CreationKit.log",
            data_path / "Logs" / "CreationKit.log"
        ]
        
        for log_path in possible_log_paths:
            if log_path.exists():
                try:
                    with open(log_path, encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        for pattern in completion_patterns:
                            if pattern in content:
                                logger.error(f"Found completion failure pattern '{pattern}' in {log_path}")
                                return False
                except Exception as e:
                    logger.warning(f"Could not read log file {log_path}: {e}")
                    
        return True