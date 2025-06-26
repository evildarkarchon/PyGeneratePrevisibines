from __future__ import annotations

import shutil
import time
from collections.abc import Callable
from pathlib import Path

from PrevisLib.utils.logging import get_logger

logger = get_logger(__name__)


def clean_directory(directory: Path, create: bool = True) -> None:
    if directory.exists():
        logger.debug(f"Cleaning directory: {directory}")
        shutil.rmtree(directory)
    
    if create:
        logger.debug(f"Creating directory: {directory}")
        directory.mkdir(parents=True, exist_ok=True)


def ensure_directory(directory: Path) -> None:
    if not directory.exists():
        logger.debug(f"Creating directory: {directory}")
        directory.mkdir(parents=True, exist_ok=True)


def is_directory_empty(directory: Path) -> bool:
    if not directory.exists():
        return True
    return not any(directory.iterdir())


def wait_for_file(file_path: Path, timeout: float = 30.0, check_interval: float = 0.5) -> bool:
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if file_path.exists():
            return True
        time.sleep(check_interval)
    
    return False


def mo2_aware_move(source: Path, destination: Path, delay: float = 2.0) -> None:
    logger.debug(f"Moving {source} to {destination} (MO2 delay: {delay}s)")
    
    shutil.move(str(source), str(destination))
    
    time.sleep(delay)


def mo2_aware_copy(source: Path, destination: Path, delay: float = 2.0) -> None:
    logger.debug(f"Copying {source} to {destination} (MO2 delay: {delay}s)")
    
    if source.is_dir():
        shutil.copytree(source, destination, dirs_exist_ok=True)
    else:
        shutil.copy2(source, destination)
    
    time.sleep(delay)


def find_files(directory: Path, pattern: str = "*", recursive: bool = True) -> list[Path]:
    if recursive:
        return list(directory.rglob(pattern))
    return list(directory.glob(pattern))


def count_files(directory: Path, pattern: str = "*", recursive: bool = True) -> int:
    return len(find_files(directory, pattern, recursive))


def safe_delete(file_path: Path, retry_count: int = 3, retry_delay: float = 1.0) -> bool:
    """Safely delete a file or directory with retries."""
    for attempt in range(retry_count):
        try:
            if file_path.exists():
                if file_path.is_dir():
                    shutil.rmtree(file_path)
                else:
                    file_path.unlink()
                logger.debug(f"Deleted: {file_path}")
                return True
            return True  # Already gone
        except Exception as e:
            if attempt < retry_count - 1:
                logger.warning(f"Failed to delete {file_path} (attempt {attempt + 1}/{retry_count}): {e}")
                time.sleep(retry_delay)
            else:
                logger.error(f"Failed to delete {file_path} after {retry_count} attempts: {e}")
    return False


def copy_with_callback(
    source: Path,
    destination: Path,
    callback: Callable[[int, int], None] | None = None,
) -> None:
    if source.is_dir():
        files = list(source.rglob("*"))
        total = len(files)
        
        for i, file in enumerate(files):
            if file.is_file():
                rel_path = file.relative_to(source)
                dest_file = destination / rel_path
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file, dest_file)
                
                if callback:
                    callback(i + 1, total)
    else:
        shutil.copy2(source, destination)
        if callback:
            callback(1, 1)