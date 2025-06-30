"""xEdit/FO4Edit wrapper for previs operations."""

import os
import subprocess
import time
from pathlib import Path
from subprocess import Popen
from typing import Any, Literal, Self

from loguru import logger

from PrevisLib.utils.process import ProcessRunner

try:
    from pywinauto import Application  # type: ignore[reportMissingImports, import-not-found]
    from pywinauto.timings import TimeoutError as PywinautoTimeoutError  # type: ignore[reportMissingImports, import-not-found]

    PYWINAUTO_AVAILABLE = True
except ImportError:
    PYWINAUTO_AVAILABLE = False
    logger.warning("pywinauto not available - xEdit automation will be limited")

    # Create stubs for pywinauto classes/functions
    class WindowStub:
        def exists(self) -> Literal[False]:
            return False

        def window_text(self) -> Literal[""]:
            return ""

        def close(self) -> None:
            pass

        def child_window(self, control_type: Any = None) -> Self:  # noqa: ARG002
            return self

        def descendants(self, control_type: Any = None) -> list[Any]:  # noqa: ARG002
            return []

    class Application:
        def __init__(self, backend: str = "uia") -> None:
            pass

        def connect(self, process: Any = None) -> Self:  # noqa: ARG002
            return self

        def window(self, title_re: Any = None) -> WindowStub:  # noqa: ARG002
            return WindowStub()

    class PywinautoTimeoutError(Exception):
        pass


class XEditWrapper:
    """Wrapper for xEdit/FO4Edit operations."""

    def __init__(self, xedit_path: Path, plugin_name: str) -> None:
        self.xedit_path = xedit_path
        self.plugin_name = plugin_name
        self.process_runner = ProcessRunner()
        # File system operations will use module functions directly

    def merge_combined_objects(self, data_path: Path, script_path: Path) -> bool:
        """
        Merges combined objects using xEdit. This function executes xEdit
        with specified arguments and automates the merge process. It checks
        the xEdit logs for errors after the process and returns whether the
        merge operation was successful.

        :param data_path: Path to the data directory where the relevant files are located.
        :type data_path: Path
        :param script_path: Path to the script file to be executed by xEdit.
        :type script_path: Path
        :return: True if the combined objects merge completed successfully,
            False otherwise.
        :rtype: bool
        """
        logger.info("Starting combined objects merge with xEdit")

        args = [
            str(self.xedit_path),
            "-IKnowWhatImDoing",
            "-AllowMasterFilesEdit",
            f"-D:{data_path}",
            f"-script:{script_path.stem}",
            self.plugin_name,
        ]

        if PYWINAUTO_AVAILABLE:
            success: bool = self._run_with_automation(args, "Merge Combined Objects")
        else:
            success = self.process_runner.execute(
                args,
                timeout=1200,  # 20 minutes
                show_output=True,
            )

        if success:
            if self._check_xedit_log("combined objects merge"):
                logger.success("Combined objects merge completed successfully")
            else:
                logger.error("Combined objects merge reported errors")
                return False
        else:
            logger.error("xEdit combined objects merge failed")

        return success

    def merge_previs(self, data_path: Path, script_path: Path) -> bool:
        """
        Merge previs data using xEdit, running the process either with automation or
        through the process runner depending on the availability of Pywinauto. This
        method will orchestrate the merge process, run the required script, and
        validate the xEdit log for successful completion of the merge operation.

        :param data_path: The file system path to the data directory used for the
            previs merging process.
        :type data_path: Path
        :param script_path: The file system path to the script required for the
            previs merging operation, specified as a Path object.
        :type script_path: Path
        :return: True if the previs merge was successful, otherwise False.
        :rtype: bool
        """
        logger.info("Starting previs data merge with xEdit")

        args: list[str] = [
            str(self.xedit_path),
            f"-D:{data_path}",
            f"-script:{script_path.stem}",
            self.plugin_name,
        ]

        if PYWINAUTO_AVAILABLE:
            success: bool = self._run_with_automation(args, "Merge Previs")
        else:
            success = self.process_runner.execute(
                args,
                timeout=1200,  # 20 minutes
                show_output=True,
            )

        if success:
            if self._check_xedit_log("previs merge"):
                logger.success("Previs data merge completed successfully")
            else:
                logger.error("Previs data merge reported errors")
                return False
        else:
            logger.error("xEdit previs merge failed")

        return success

    def _run_with_automation(self, args: list[str], operation_name: str) -> bool:
        """
        Executes an operation using automation with xEdit if available; otherwise, falls back
        to standard execution. The process includes starting xEdit, monitoring for completion,
        and handling any issues such as errors or timeouts that may occur during the execution.

        :param args: List of command-line arguments for executing the operation
            with xEdit.
        :type args: list[str]
        :param operation_name: The name of the operation being performed, for
            logging and identification purposes.
        :type operation_name: str
        :return: A boolean indicating whether the operation was successfully
            completed. Returns True if the operation was successful, and False
            otherwise.
        :rtype: bool
        """
        if not PYWINAUTO_AVAILABLE:
            logger.warning("pywinauto not available, falling back to standard execution")
            return self.process_runner.execute(args, timeout=1200, show_output=True)

        try:
            logger.info(f"Starting xEdit with automation for {operation_name}")

            # Start xEdit process
            process: Popen[bytes] = subprocess.Popen(args)
            time.sleep(3)  # Give xEdit time to start

            # Connect to xEdit window
            app: Application = Application(backend="uia").connect(process=process.pid)
            main_window: WindowStub = app.window(title_re=".*Edit.*")

            # Wait for script completion
            max_wait: float = 1200  # 20 minutes
            start_time: float = time.time()

            while time.time() - start_time < max_wait:
                try:
                    # Look for completion indicators
                    if main_window.exists():
                        # Check if any dialogs appeared
                        dialogs: list[WindowStub] = main_window.descendants(control_type="Window")
                        for dialog in dialogs:
                            title: str = dialog.window_text()
                            if "error" in title.lower() or "exception" in title.lower():
                                logger.error(f"Error dialog detected: {title}")
                                try:  # noqa: SIM105
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
            return_code: int = process.wait(timeout=10)

        except (subprocess.SubprocessError, PywinautoTimeoutError, OSError, TimeoutError) as e:
            logger.error(f"Window automation failed: {e}")
            return False
        else:
            return return_code == 0

    def _is_xedit_busy(self, window) -> bool:  # noqa: ANN001
        """
        Determine whether the XEdit application window is busy based on the status bar
        text. If the status bar indicates "processing" or "running", the method returns
        True. If an exception occurs or no such indication is found, it returns False.

        :param window: The application window object to evaluate.
        :type window: WindowStub
        :return: True if the application is busy as per the status bar, False otherwise.
        :rtype: bool
        """
        try:
            # Check status bar or other indicators
            status_bar: WindowStub = window.child_window(control_type="StatusBar")
            if status_bar.exists():
                status_text: str = status_bar.window_text()
                if "processing" in status_text.lower() or "running" in status_text.lower():
                    return True
        except:
            pass

        return False

    def _check_xedit_log(self, operation: str) -> bool:
        """
        Checks xEdit logs to determine the success or failure of an operation, following specific
        patterns defined in the batch file logic. This method reviews logs from various possible
        locations and examines their contents to identify error patterns or completion indicators.

        :param operation: The operation identifier or description being checked in the xEdit logs.
        :type operation: str
        :return: Boolean indicating whether the operation was successful. Returns True if successful
                 or no errors are found, False otherwise.
        :rtype: bool
        :raises OSError: If there is an issue reading log files from disk.
        :raises UnicodeDecodeError: If the log files contain non-UTF-8 decodable content.
        """
        # Enhanced to match the batch file patterns exactly
        # Look for the unattended log file that xEdit creates
        temp_dir = Path(os.environ.get("TEMP", os.environ.get("TMP", str(Path.home() / "temp"))))
        unattended_log = temp_dir / "UnattendedScript.log"

        # Also check other possible log locations
        possible_log_paths: list[Path] = [
            unattended_log,  # Primary location matching batch file
            self.xedit_path.parent / "Edit Scripts" / "Edit Logs" / f"{self.plugin_name}.log",
        ]

        # Enhanced patterns to match the batch file exactly
        error_patterns: list[str] = [
            "Error: ",  # Exact match from batch file
            "Exception:",
            "Failed:",
            "Could not",
        ]

        completion_patterns: list[str] = [
            "Completed: No Errors.",  # Exact match from batch file - indicates success
            "Completed: ",  # Exact match from batch file - general completion
        ]

        for log_path in possible_log_paths:
            if log_path.exists():
                try:
                    with log_path.open(encoding="utf-8", errors="ignore") as f:
                        content: str = f.read()

                        # Check for errors first (matching batch file logic)
                        for pattern in error_patterns:
                            if pattern in content:
                                logger.error(f"Found error pattern '{pattern}' in xEdit log: {log_path}")
                                return False

                        # Check for completion indicators
                        found_completion = False
                        for pattern in completion_patterns:
                            if pattern in content:
                                found_completion = True
                                if pattern == "Completed: No Errors.":
                                    logger.info(f"xEdit completed successfully: {pattern}")
                                    return True
                                if pattern == "Completed: ":
                                    # General completion - may have warnings but not errors
                                    logger.info(f"xEdit completed with possible warnings: {pattern}")
                                    return True

                        # If we found the log but no completion indicator, it may have failed
                        if log_path == unattended_log and not found_completion:
                            logger.error(f"xEdit script {operation} failed - no completion indicator found")
                            return False

                except (OSError, UnicodeDecodeError) as e:
                    logger.warning(f"Could not read log file {log_path}: {e}")

        # If no unattended log found, warn but assume success for backwards compatibility
        logger.warning(f"Could not find xEdit unattended log for {operation} - assuming success")
        return True
