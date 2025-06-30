from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import types

    from loguru import Logger

    from PrevisLib.models.data_classes import ToolPaths

from PrevisLib.utils.logging import get_logger

logger: Logger = get_logger(__name__)


def find_tool_paths() -> ToolPaths:
    """
    Find and return paths to various tools based on system configuration.

    This function attempts to locate paths for specific tools required by the application,
    such as xEdit, Fallout4, Creation Kit, Archive2, and BSArch. On Windows platforms,
    it retrieves the paths using the Windows Registry. If the platform is not Windows or
    the required tools cannot be found, it returns an instance of `ToolPaths` with default
    (empty) attributes.

    The method will log warnings or errors if the platform is not supported, the `winreg`
    module cannot be imported, or if certain tools are not found.

    :return: An instance of `ToolPaths` containing located paths for the tools.
    :rtype: ToolPaths
    """
    from PrevisLib.models.data_classes import ToolPaths

    paths: ToolPaths = ToolPaths()

    if sys.platform != "win32":
        logger.warning("Registry reading is only available on Windows. Manual path configuration required.")
        return paths

    try:
        import winreg
    except ImportError:
        logger.error("winreg module not available. Cannot read registry.")
        return paths

    paths.xedit = _find_xedit_path(winreg)
    paths.fallout4, paths.creation_kit = _find_fallout4_paths(winreg)

    if paths.fallout4:
        archive_path: Path = paths.fallout4.parent / "Tools" / "Archive2" / "Archive2.exe"
        if archive_path.exists():
            paths.archive2 = archive_path

        bsarch_path: Path | None = paths.xedit.parent / "BSArch.exe" if paths.xedit else None
        if bsarch_path and bsarch_path.exists():
            paths.bsarch = bsarch_path

    return paths


def _find_xedit_path(winreg: types.ModuleType) -> Path | None:
    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"FO4Script\DefaultIcon") as key:
            value, _ = winreg.QueryValueEx(key, "")
            # In Python 3.12, create_autospec with a spec containing a method that returns a tuple of (str, int)
            # will result in a mock that returns a tuple of (MagicMock, MagicMock) instead.
            # This is a workaround for that behavior.
            if isinstance(value, str) and Path(value).exists():
                logger.debug(f"Found xEdit at: {value}")
                return Path(value)
    except (OSError, ValueError) as e:
        logger.debug(f"Failed to find xEdit in registry: {e}")

    for name in ["FO4Edit64.exe", "xEdit64.exe", "FO4Edit.exe", "xEdit.exe"]:
        local_path = Path.cwd() / name
        if local_path.exists():
            logger.debug(f"Found xEdit in current directory: {name}")
            return local_path.absolute()

    return None


def _find_fallout4_paths(winreg: types.ModuleType) -> tuple[Path | None, Path | None]:
    """
    Finds the paths of Fallout 4 and Creation Kit executables by querying the Windows registry.

    This function attempts to locate the installation directory for Fallout 4 by querying
    the registry key under r"HKEY_LOCAL_MACHINE\SOFTWARE\Wow6432Node\Bethesda Softworks\Fallout4".
    It specifically checks for the "installed path" value, and if found, verifies the existence
    of the executables for Fallout 4 and Creation Kit within that directory.

    :param winreg: The Windows Registry module used to interact with system registry entries.
    :type winreg: types.ModuleType
    :return: A tuple containing the `Path` of the Fallout 4 executable and the `Path` of the
        Creation Kit executable. If either is not found, the corresponding value in the tuple
        will be `None`.
    :rtype: tuple[Path | None, Path | None]
    """
    fallout4_path: Path | None = None
    ck_path: Path | None = None

    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\Bethesda Softworks\Fallout4") as key:
            install_path, _ = winreg.QueryValueEx(key, "installed path")
            if install_path:
                install_path_p: Path = Path(install_path)
                fo4_exe: Path = install_path_p / "Fallout4.exe"
                ck_exe: Path = install_path_p / "CreationKit.exe"

                if fo4_exe.exists():
                    fallout4_path = fo4_exe
                    logger.debug(f"Found Fallout 4 at: {fallout4_path}")

                if ck_exe.exists():
                    ck_path = ck_exe
                    logger.debug(f"Found Creation Kit at: {ck_path}")
    except (OSError, ValueError) as e:
        logger.debug(f"Failed to find Fallout 4 in registry: {e}")

    return fallout4_path, ck_path