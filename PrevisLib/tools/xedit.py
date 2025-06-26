"""xEdit/FO4Edit wrapper for previs operations."""

import time
from pathlib import Path

from loguru import logger

from ..utils.process import ProcessRunner

try:
    from pywinauto import Application
    from pywinauto.timings import TimeoutError as PywinautoTimeoutError
    PYWINAUTO_AVAILABLE = True
except ImportError:
    PYWINAUTO_AVAILABLE = False
    logger.warning("pywinauto not available - xEdit automation will be limited")


class XEditWrapper:
    """Wrapper for xEdit/FO4Edit operations."""
    
    def __init__(self, xedit_path: Path, plugin_name: str):
        self.xedit_path = xedit_path
        self.plugin_name = plugin_name
        self.process_runner = ProcessRunner()
        # File system operations will use module functions directly
        
    def merge_combined_objects(self, data_path: Path, script_path: Path) -> bool:
        """Merge combined objects using xEdit script.
        
        Args:
            data_path: Path to Fallout 4 Data directory
            script_path: Path to the merge script
            
        Returns:
            True if successful, False otherwise
        """
        logger.info("Starting combined objects merge with xEdit")
        
        args = [
            str(self.xedit_path),
            "-IKnowWhatImDoing",
            "-AllowMasterFilesEdit",
            f"-D:{data_path}",
            f"-script:{script_path.stem}",
            self.plugin_name
        ]
        
        if PYWINAUTO_AVAILABLE:
            success = self._run_with_automation(args, "Merge Combined Objects")
        else:
            success = self.process_runner.run_process(
                args,
                timeout=1200,  # 20 minutes
                show_output=True
            )
            
        if success:
            if self._check_xedit_log(data_path, "combined objects merge"):
                logger.success("Combined objects merge completed successfully")
            else:
                logger.error("Combined objects merge reported errors")
                return False
        else:
            logger.error("xEdit combined objects merge failed")
            
        return success
        
    def merge_previs(self, data_path: Path, script_path: Path) -> bool:
        """Merge previs data using xEdit script.
        
        Args:
            data_path: Path to Fallout 4 Data directory
            script_path: Path to the merge script
            
        Returns:
            True if successful, False otherwise
        """
        logger.info("Starting previs data merge with xEdit")
        
        args = [
            str(self.xedit_path),
            "-IKnowWhatImDoing",
            "-AllowMasterFilesEdit", 
            f"-D:{data_path}",
            f"-script:{script_path.stem}",
            self.plugin_name
        ]
        
        if PYWINAUTO_AVAILABLE:
            success = self._run_with_automation(args, "Merge Previs")
        else:
            success = self.process_runner.run_process(
                args,
                timeout=1200,  # 20 minutes
                show_output=True
            )
            
        if success:
            if self._check_xedit_log(data_path, "previs merge"):
                logger.success("Previs data merge completed successfully")
            else:
                logger.error("Previs data merge reported errors")
                return False
        else:
            logger.error("xEdit previs merge failed")
            
        return success
        
    def _run_with_automation(self, args: list[str], operation_name: str) -> bool:
        """Run xEdit with window automation for better control.
        
        Args:
            args: Command line arguments
            operation_name: Name of the operation for logging
            
        Returns:
            True if successful, False otherwise
        """
        if not PYWINAUTO_AVAILABLE:
            logger.warning("pywinauto not available, falling back to standard execution")
            return self.process_runner.run_process(args, timeout=1200, show_output=True)
            
        try:
            logger.info(f"Starting xEdit with automation for {operation_name}")
            
            # Start xEdit process
            import subprocess
            process = subprocess.Popen(args)
            time.sleep(3)  # Give xEdit time to start
            
            # Connect to xEdit window
            app = Application(backend="uia").connect(process=process.pid)
            main_window = app.window(title_re=".*Edit.*")
            
            # Wait for script completion
            max_wait = 1200  # 20 minutes
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                try:
                    # Look for completion indicators
                    if main_window.exists():
                        # Check if any dialogs appeared
                        dialogs = main_window.descendants(control_type="Window")
                        for dialog in dialogs:
                            title = dialog.window_text()
                            if "error" in title.lower() or "exception" in title.lower():
                                logger.error(f"Error dialog detected: {title}")
                                try:
                                    # Try to close error dialog
                                    dialog.close()
                                except:
                                    pass
                                return False
                                
                        # Check if xEdit is still busy
                        if not self._is_xedit_busy(main_window):
                            logger.info("xEdit appears to have finished processing")
                            break
                            
                except PywinautoTimeoutError:
                    pass
                    
                time.sleep(2)
                
            # Close xEdit
            try:
                main_window.close()
                time.sleep(2)
            except:
                # Force terminate if needed
                process.terminate()
                
            # Check exit code
            return_code = process.wait(timeout=10)
            return return_code == 0
            
        except Exception as e:
            logger.error(f"Window automation failed: {e}")
            return False
            
    def _is_xedit_busy(self, window) -> bool:
        """Check if xEdit is still processing.
        
        Args:
            window: xEdit main window
            
        Returns:
            True if busy, False if idle
        """
        try:
            # Check status bar or other indicators
            status_bar = window.child_window(control_type="StatusBar")
            if status_bar.exists():
                status_text = status_bar.window_text()
                if "processing" in status_text.lower() or "running" in status_text.lower():
                    return True
        except:
            pass
            
        return False
        
    def _check_xedit_log(self, data_path: Path, operation: str) -> bool:
        """Check xEdit log for successful completion.
        
        Args:
            data_path: Path to Fallout 4 Data directory
            operation: Name of the operation
            
        Returns:
            True if successful, False if errors found
        """
        # Look for xEdit logs
        possible_log_paths = [
            self.xedit_path.parent / "Edit Scripts" / "Edit Logs" / f"{self.plugin_name}.log",
            data_path / "Edit Scripts" / "Edit Logs" / f"{self.plugin_name}.log",
            Path.home() / "Documents" / "My Games" / "Fallout4" / "Edit Logs" / f"{self.plugin_name}.log"
        ]
        
        success_patterns = [
            "Done processing",
            "Finished",
            "completed successfully",
            "Process completed"
        ]
        
        error_patterns = [
            "Error:",
            "Exception:",
            "Failed:",
            "Could not"
        ]
        
        for log_path in possible_log_paths:
            if log_path.exists():
                try:
                    with open(log_path, encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                        # Check for errors first
                        for pattern in error_patterns:
                            if pattern in content:
                                logger.error(f"Found error pattern '{pattern}' in xEdit log")
                                return False
                                
                        # Check for success indicators
                        for pattern in success_patterns:
                            if pattern in content:
                                logger.info(f"Found success pattern '{pattern}' in xEdit log")
                                return True
                                
                except Exception as e:
                    logger.warning(f"Could not read log file {log_path}: {e}")
                    
        logger.warning(f"Could not find xEdit log for {operation}")
        return True  # Assume success if no log found