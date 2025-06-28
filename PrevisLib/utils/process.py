from __future__ import annotations

import subprocess
import sys
import time
from subprocess import CompletedProcess
from typing import TYPE_CHECKING, Any

from PrevisLib.utils.logging import get_logger

if TYPE_CHECKING:
    from pathlib import Path

    from loguru import Logger

logger: Logger = get_logger(__name__)


class ProcessResult:
    def __init__(
        self,
        returncode: int,
        stdout: str,
        stderr: str,
        elapsed_time: float,
    ) -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.elapsed_time = elapsed_time
        self.success = returncode == 0


def run_process(  # noqa: PLR0913
    command: list[str] | str,
    cwd: Path | None = None,
    timeout: float | None = None,
    capture_output: bool = True,
    shell: bool = False,
    env: dict[str, str] | None = None,
) -> ProcessResult:
    command_str: str | list[str]
    if isinstance(command, str):
        command_str = command
        if not shell:
            command = command.split()
    else:
        command_str = " ".join(command)

    logger.debug(f"Running command: {command_str}")
    if cwd:
        logger.debug(f"Working directory: {cwd}")

    start_time: float = time.time()

    try:
        if capture_output:
            result: CompletedProcess[str] = subprocess.run(
                command,
                check=False,
                cwd=cwd,
                timeout=timeout,
                capture_output=True,
                text=True,
                shell=shell,
                env=env,
            )
        else:
            result = subprocess.run(
                command,
                check=False,
                cwd=cwd,
                timeout=timeout,
                shell=shell,
                env=env,
                text=True,
            )
            result.stdout = ""
            result.stderr = ""

        elapsed_time = time.time() - start_time

        process_result: ProcessResult = ProcessResult(
            returncode=result.returncode,
            stdout=result.stdout if capture_output else "",
            stderr=result.stderr if capture_output else "",
            elapsed_time=elapsed_time,
        )

        if process_result.success:
            logger.debug(f"Command completed successfully in {elapsed_time:.2f}s")
        else:
            logger.error(f"Command failed with return code {result.returncode}")
            if capture_output and result.stderr:
                logger.error(f"Error output: {result.stderr}")

    except subprocess.TimeoutExpired:
        elapsed_time: float = time.time() - start_time
        logger.error(f"Command timed out after {elapsed_time:.2f}s")
        return ProcessResult(
            returncode=-1,
            stdout="",
            stderr=f"Process timed out after {timeout}s",
            elapsed_time=elapsed_time,
        )
    except (OSError, ValueError) as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Failed to run command: {e}")
        return ProcessResult(
            returncode=-1,
            stdout="",
            stderr=str(e),
            elapsed_time=elapsed_time,
        )
    else:
        return process_result


class ProcessRunner:
    """Wrapper class for process execution utilities."""

    def execute(self, command: list[str] | str, timeout: float | None = None, show_output: bool = False, cwd: Path | None = None) -> bool:
        """Execute a process and return success status.

        Args:
            command: Command to run
            timeout: Timeout in seconds
            show_output: Whether to show output to console
            cwd: Working directory

        Returns:
            True if successful, False otherwise
        """
        result: ProcessResult = run_process(command=command, cwd=cwd, timeout=timeout, capture_output=not show_output, shell=False)
        return result.success


def check_process_running(process_name: str) -> bool:
    try:
        import psutil

        for proc in psutil.process_iter(["name"]):
            if proc.info["name"] and process_name.lower() in proc.info["name"].lower():
                return True
    except ImportError:
        logger.warning("psutil not available, cannot check running processes")
    except (OSError, AttributeError) as e:
        logger.error(f"Error checking process: {e}")
    except Exception as e:  # noqa: BLE001
        logger.error(f"Unexpected error checking process: {e}")

    return False


def kill_process(process_name: str) -> bool:
    try:
        import psutil

        killed = False
        for proc in psutil.process_iter(["name"]):
            if proc.info["name"] and process_name.lower() in proc.info["name"].lower():
                logger.info(f"Killing process: {proc.info['name']} (PID: {proc.pid})")
                proc.kill()
                killed = True

        return killed  # noqa: TRY300
    except ImportError:
        logger.warning("psutil not available, cannot kill processes")
    except (OSError, AttributeError) as e:
        logger.error(f"Error killing process: {e}")

    return False


def run_with_window_automation(
    command: list[str] | str,
    window_title: str,
    automation_func: Any = None,
    cwd: Path | None = None,
    timeout: float = 300.0,
) -> ProcessResult:
    if sys.platform != "win32":
        logger.error("Window automation is only supported on Windows")
        return ProcessResult(
            returncode=-1,
            stdout="",
            stderr="Window automation not supported on this platform",
            elapsed_time=0.0,
        )

    try:
        from pywinauto.application import Application  # type: ignore[reportMissingImports, import-not-found]
    except ImportError:
        logger.error("pywinauto not available for window automation")

        # Create stubs for pywinauto classes
        class WindowStub:
            def wait(self, condition: str, timeout: float = 30) -> None:
                pass

            def wait_not(self, condition: str, timeout: float = 300) -> None:
                pass

        class Application:
            def __init__(self, backend: str = "win32") -> None:
                pass

            def start(self, cmd_line: str, work_dir: str | None = None) -> "Application":  # noqa: ARG002, UP037
                return self

            def window(self, title_re: str) -> WindowStub:  # noqa: ARG002
                return WindowStub()

        return ProcessResult(
            returncode=-1,
            stdout="",
            stderr="pywinauto not installed",
            elapsed_time=0.0,
        )

    logger.info(f"Starting process with window automation: {window_title}")

    command_str: str = " ".join(command) if isinstance(command, list) else command

    try:
        app: Application | Any = Application(backend="win32").start(command_str, work_dir=str(cwd) if cwd else None)

        time.sleep(2)

        window: WindowStub | Any = app.window(title_re=f".*{window_title}.*")
        window.wait("ready", timeout=30)

        if automation_func:
            automation_func(window)

        window.wait_not("exists", timeout=timeout)

        return ProcessResult(
            returncode=0,
            stdout="",
            stderr="",
            elapsed_time=timeout,
        )

    except (OSError, AttributeError, ValueError) as e:
        logger.error(f"Window automation failed: {e}")
        return ProcessResult(
            returncode=-1,
            stdout="",
            stderr=str(e),
            elapsed_time=0.0,
        )
