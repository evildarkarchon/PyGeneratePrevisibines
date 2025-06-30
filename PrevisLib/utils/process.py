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
    """
    Executes a shell command or a list of commands as a subprocess with customizable options such as
    working directory, timeout, output capturing, and environment variables.

    The function monitors the execution time and logs detailed debugging information, including
    input commands, execution time, and any output or errors from the process. It ensures robust
    error handling for timeouts and unexpected issues during the subprocess execution.

    :param command: The command to execute. Can be a single string or a list of strings
        representing the command and its arguments.
    :type command: list[str] | str
    :param cwd: The working directory to run the command in. If None, uses the current working
        directory.
    :type cwd: Path | None
    :param timeout: The maximum execution time allowed for the command in seconds. If the command
        exceeds this time, it will be terminated. If None, no timeout is applied.
    :type timeout: float | None
    :param capture_output: If True, captures the standard output and standard error of the
        command. Otherwise, no output is captured.
    :type capture_output: bool
    :param shell: If True, the command string will be executed through the shell. Use with caution
        as this may introduce security risks.
    :type shell: bool
    :param env: A dictionary of environment variables to use for the command execution. If None,
        the parent process's environment variables are used.
    :type env: dict[str, str] | None
    :return: A ProcessResult object containing the result of the command execution. Includes the
        return code, standard output, standard error, and elapsed execution time.
    :rtype: ProcessResult
    """
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

    start_time: float = time.perf_counter()

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

        elapsed_time = time.perf_counter() - start_time

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
        elapsed_time: float = time.perf_counter() - start_time
        logger.error(f"Command timed out after {elapsed_time:.2f}s")
        return ProcessResult(
            returncode=-1,
            stdout="",
            stderr=f"Process timed out after {timeout}s",
            elapsed_time=elapsed_time,
        )
    except (OSError, ValueError) as e:
        elapsed_time = time.perf_counter() - start_time
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
        """
        Executes a system command using the specified parameters and returns the success
        status of the process. The function provides control over the command execution
        with options for timeout, output display, and working directory.

        :param command: Command to execute on the system. Can be a list of command arguments
                        or a single command string.
        :param timeout: Maximum time, in seconds, to wait for the process to complete.
                        If None, it will wait indefinitely.
        :param show_output: Whether to display the command's output to the console.
                            If False, the output will be captured silently.
        :param cwd: The working directory in which the command should be executed.
                    If None, it defaults to the current directory.
        :return: True if the process executed successfully, otherwise False.
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
    """
    Kills a running process with the specified name. This function iterates through all
    running processes and checks if their name matches or contains the given process name.
    If a match is found, the process is terminated.

    :param process_name: The name of the process to be terminated.
    :type process_name: str

    :return: True if at least one process was successfully killed, False otherwise.
    :rtype: bool
    """
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
    """
    Runs a command with window automation on Windows using `pywinauto` if available. This function starts
    a specified process, waits for the associated window to become ready, applies an optional automation
    function, and waits until the window no longer exists or the timeout is reached.

    :param command: The command to execute, either as a list of strings (for argument separation) or a single string.
    :param window_title: The title (or part of the title) of the window to interact with.
    :param automation_func: An optional callable to apply additional automation to the window. The callable
        should accept a `Window` object or equivalent for interaction.
    :param cwd: An optional `Path` object specifying the working directory in which to run the command.
    :param timeout: The maximum time, in seconds, to wait for the window to close after automation operations.
        Defaults to 300 seconds.
    :return: A `ProcessResult` object containing process return code, stdout, stderr,
        and elapsed time of the automation task.
    """
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
