from __future__ import annotations

import shutil
import time
from typing import TYPE_CHECKING

from PrevisLib.utils.logging import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from loguru import Logger

logger: Logger = get_logger(__name__)


def clean_directory(directory: Path, create: bool = True) -> None:
    """
    Cleans a specified directory by removing all its contents. If the directory does not exist,
    it can optionally be created. This function utilizes debugging logs to detail its operations.

    :param directory: The path of the directory to be cleaned.
    :param create: A flag indicating whether to create the directory if it does not exist.
    :return: None
    """
    if directory.exists():
        logger.debug(f"Cleaning directory: {directory}")
        shutil.rmtree(directory)

    if create:
        logger.debug(f"Creating directory: {directory}")
        directory.mkdir(parents=True, exist_ok=True)


def ensure_directory(directory: Path) -> None:
    """
    Ensures that the specified directory exists. If the directory does not exist, it is created
    including any necessary parent directories.

    :param directory: The path of the directory to check or create.
    :type directory: Path
    :return: None
    """
    if not directory.exists():
        logger.debug(f"Creating directory: {directory}")
        directory.mkdir(parents=True, exist_ok=True)


def is_directory_empty(directory: Path) -> bool:
    """
    Checks if the specified directory is empty.

    This function determines whether the given directory exists and contains no files
    or subdirectories. If the directory does not exist, it is considered empty.

    :param directory: The Path object representing the directory to check.
    :type directory: Path
    :return: True if the directory is empty or does not exist, otherwise False.
    :rtype: bool
    """
    if not directory.exists():
        return True
    return not any(directory.iterdir())


def wait_for_file(file_path: Path, timeout: float = 30.0, check_interval: float = 0.5) -> bool:
    """
    Waits for a file to exist within a specified timeout, periodically checking
    for its presence.

    This function monitors the specified file path to determine whether the file
    exists. It performs the check in intervals defined by ``check_interval``, and
    the function will block for at most the duration defined by ``timeout``. If
    the file exists within the timeout period, the function returns True.
    Otherwise, it returns False after the timeout is reached.

    :param file_path: The path of the file to monitor.
    :type file_path: Path
    :param timeout: The maximum time to wait for the file to exist, in seconds.
    :type timeout: float, optional
    :param check_interval: The time interval, in seconds, between successive checks
        for the file's existence.
    :type check_interval: float, optional
    :return: True if the file exists within the timeout duration, otherwise False.
    :rtype: bool
    """
    start_time: float = time.time()

    while time.time() - start_time < timeout:
        if file_path.exists():
            return True
        time.sleep(check_interval)

    return False


def wait_for_output_file(file_path: Path, timeout: float = 30.0, check_interval: float = 0.5) -> bool:
    """
    Waits for the specified output file to be created within a given timeout period,
    with an optional interval for checking the file existence. Additionally, if
    ModOrganizer is detected running, it adjusts the timeout and check interval to
    ensure compatibility. It also applies an initial delay to accommodate ModOrganizer's
    Virtual File System setup time.

    :param file_path: Path of the file to check for existence.
    :param timeout: Maximum time in seconds to wait for the file to be created.
        Defaults to 30.0 seconds.
    :param check_interval: Interval in seconds for checking the file existence.
        Defaults to 0.5 seconds.
    :return: True if the file is found within the timeout period, False otherwise.
    """
    from PrevisLib.utils.process import check_process_running

    # Check if ModOrganizer is running
    mo2_running: bool = check_process_running("ModOrganizer")

    if mo2_running:
        logger.info(f"ModOrganizer detected - using extended delay for {file_path.name}")
        # Use longer timeout and check interval for MO2
        timeout = max(timeout, 10.0)  # Minimum 10 seconds
        check_interval = max(check_interval, 1.0)  # Check every second

        # Add initial delay to let MO2 VFS catch up
        time.sleep(3.0)

    start_time: float = time.time()

    while time.time() - start_time < timeout:
        # Check for case-insensitive file existence
        if _file_exists_case_insensitive(file_path):
            if mo2_running:
                logger.info(f"Found {file_path.name} after {time.time() - start_time:.1f}s")
            return True
        time.sleep(check_interval)

    return False


def _file_exists_case_insensitive(file_path: Path) -> bool:
    """
    Checks if a file exists in a case-insensitive manner by verifying the existence
    of the file or searching for a case-insensitive match within the parent directory.

    :param file_path: The path to the file being checked for existence.
    :type file_path: Path

    :return: True if the file exists either directly or through a case-insensitive
        match in the parent directory, False otherwise.
    :rtype: bool
    """
    if file_path.exists():
        return True

    # Check parent directory for case-insensitive match
    parent: Path = file_path.parent
    if not parent.exists():
        return False

    target_name: str = file_path.name.lower()
    return any(item.name.lower() == target_name for item in parent.iterdir())


def mo2_aware_move(source: Path, destination: Path, delay: float = 2.0) -> None:
    """
    Moves a file or directory from a source path to a destination path with a delay in
    Mind of Oblivion 2 (MO2) operations. This function performs the move operation
    using Python's shutil module and introduces a delay after the operation to account
    for MO2-specific considerations.

    :param source: The source path of the file or directory to move.
    :type source: Path
    :param destination: The destination path where the file or directory should be moved.
    :type destination: Path
    :param delay: The time in seconds to wait after performing the move operation. This
        is specific to MO2 operations. Defaults to 2.0 seconds.
    :type delay: float
    :return: None
    """
    logger.debug(f"Moving {source} to {destination} (MO2 delay: {delay}s)")

    shutil.move(str(source), str(destination))

    time.sleep(delay)


def mo2_aware_copy(source: Path, destination: Path, delay: float = 2.0) -> None:
    """
    Copies a file or directory from the source to the destination with an optional delay.
    If the source is a directory, the entire directory is copied. If the source is a file,
    the file is copied. The function incorporates a delay after the copy operation to ensure
    compatibility with MO2 (Mod Organizer 2) or other similar systems, which may require
    such delays for stability.

    :param source: The path to the source file or directory to be copied.
    :type source: Path
    :param destination: The target path where the file or directory is to be copied.
    :type destination: Path
    :param delay: The delay in seconds after the copy operation, default is 2.0 seconds.
                 It ensures synchronization with MO2 or other systems requiring delays.
    :type delay: float
    :return: No value is returned.
    :rtype: None
    """
    logger.debug(f"Copying {source} to {destination} (MO2 delay: {delay}s)")

    if source.is_dir():
        shutil.copytree(source, destination, dirs_exist_ok=True)
    else:
        shutil.copy2(source, destination)

    time.sleep(delay)


def find_files(directory: Path, pattern: str = "*", recursive: bool = True) -> list[Path]:
    """
    Searches for files within a directory that match a specified pattern.

    This function allows for both recursive and non-recursive search based on the
    value of the `recursive` parameter. The search uses the provided directory as
    the base location and retrieves file paths that match the given pattern.
    A list of matched file paths is returned.

    :param directory: The directory where the file search will be performed.
    :type directory: Path
    :param pattern: The pattern to match files against. Defaults to '*', which matches all files.
    :type pattern: str
    :param recursive: Determines whether the search should be recursive or not. Defaults to True.
    :type recursive: bool
    :return: A list of paths to files that match the pattern within the given directory.
    :rtype: list[Path]
    """
    if recursive:
        return list(directory.rglob(pattern))
    return list(directory.glob(pattern))


def count_files(directory: Path, pattern: str = "*", recursive: bool = True) -> int:
    """
    Counts the number of files in the specified directory matching the given pattern.

    This function searches for files in a specified directory that match a
    given pattern and returns the count of those files. By default, the
    pattern is set to match all files, and the search is conducted recursively
    within the directory. It uses helper functionality to perform the file
    search internally.

    :param directory: The directory in which to search for files. Must be a valid path.
    :type directory: Path
    :param pattern: The pattern used to match files. Defaults to "*".
    :type pattern: str
    :param recursive: Determines whether the search should include subdirectories.
        Defaults to True.
    :type recursive: bool
    :return: The number of files matching the specified pattern in the given
        directory.
    :rtype: int
    """
    return len(find_files(directory, pattern, recursive))


def safe_delete(file_path: Path, retry_count: int = 3, retry_delay: float = 1.0) -> bool:
    """
    Attempts to safely delete a file or directory at the specified path. If the target
    exists, it tries to delete it, handling errors such as `OSError`,
    `PermissionError`, or `FileNotFoundError`. The function will retry the deletion
    operation a specified number of times with a delay between attempts, if it
    encounters an error.

    This is useful for scenarios where deletion may temporarily fail due to
    permissions or file locks.

    :param file_path: The path to the file or directory to delete.
    :type file_path: Path
    :param retry_count: The maximum number of attempts to retry the deletion on
                        failure. Default is 3.
    :type retry_count: int
    :param retry_delay: The delay (in seconds) between retry attempts. Default is 1.0.
    :type retry_delay: float
    :return: A boolean indicating whether the deletion was successful.
    :rtype: bool
    """
    for attempt in range(retry_count):
        try:
            if file_path.exists():
                if file_path.is_dir():
                    shutil.rmtree(file_path)
                else:
                    file_path.unlink()
                logger.debug(f"Deleted: {file_path}")
                return True
        except (OSError, PermissionError, FileNotFoundError) as e:
            if attempt < retry_count - 1:
                logger.warning(f"Failed to delete {file_path} (attempt {attempt + 1}/{retry_count}): {e}")
                time.sleep(retry_delay)
            else:
                logger.error(f"Failed to delete {file_path} after {retry_count} attempts: {e}")
        else:
            return True
    return False


def copy_with_callback(
    source: Path,
    destination: Path,
    callback: Callable[[int, int], None] | None = None,
) -> None:
    """
    Copies files and directories from the source path to the destination path, with an optional
    callback to monitor the progress of the copying process.

    If the source is a directory, all files and subdirectories within it are recursively copied
    to the destination while preserving their relative paths. If the source is a single file, it
    is copied directly to the destination. An optional callback can be used to report the progress
    of the copying, specified in terms of the current item being processed and the total number
    of items.

    :param source: Source path to copy from. Can be a file or a directory.
    :type source: Path
    :param destination: Destination path to copy to.
    :type destination: Path
    :param callback: A callable to report progress, which takes two arguments:
        - the current number of items processed
        - the total number of items
        Defaults to None.
    :type callback: Callable[[int, int], None] | None
    :return: None
    """
    if source.is_dir():
        files = list(source.rglob("*"))
        total = len(files)

        for i, file in enumerate(files):
            if file.is_file():
                rel_path: Path = file.relative_to(source)
                dest_file: Path = destination / rel_path
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file, dest_file)

                if callback:
                    callback(i + 1, total)
    else:
        shutil.copy2(source, destination)
        if callback:
            callback(1, 1)
