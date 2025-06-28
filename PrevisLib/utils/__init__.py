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
from .validation import create_plugin_from_template, validate_plugin_name, validate_tool_path

__all__ = [
    "ProcessResult",
    "ProcessRunner",
    "check_process_running",
    # File system functions
    "clean_directory",
    "copy_with_callback",
    "count_files",
    "create_plugin_from_template",
    "ensure_directory",
    "find_files",
    "get_logger",
    "is_directory_empty",
    "kill_process",
    "mo2_aware_copy",
    "mo2_aware_move",
    # Process management
    "run_process",
    "safe_delete",
    # Logging
    "setup_logging",
    # Validation
    "validate_plugin_name",
    "validate_tool_path",
    "wait_for_file",
]
