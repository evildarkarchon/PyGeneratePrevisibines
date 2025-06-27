"""Utility functions for previs generation."""

from .file_system import (
    clean_directory,
    copy_with_callback,
    count_files,
    ensure_directory,
    find_files,
    is_directory_empty,
    mo2_aware_copy,
    mo2_aware_move,
    safe_delete,
    wait_for_file,
)
from .logging import get_logger
from .logging import setup_logger as setup_logging
from .process import ProcessResult, ProcessRunner, check_process_running, kill_process, run_process
from .validation import validate_plugin_name, validate_tool_path

__all__ = [
    # File system functions
    "clean_directory",
    "ensure_directory",
    "is_directory_empty",
    "wait_for_file",
    "mo2_aware_move",
    "mo2_aware_copy",
    "find_files",
    "count_files",
    "safe_delete",
    "copy_with_callback",
    # Logging
    "setup_logging",
    "get_logger",
    # Process management
    "run_process",
    "ProcessResult",
    "ProcessRunner",
    "check_process_running",
    "kill_process",
    # Validation
    "validate_plugin_name",
    "validate_tool_path",
]
