from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from loguru import Logger

    from PrevisLib.models.data_classes import ToolPaths

from PrevisLib.utils.logging import get_logger

logger: Logger = get_logger(__name__)


def find_tool_paths() -> ToolPaths:
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


def _find_xedit_path(winreg: type) -> Path | None:
    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"FO4Script\DefaultIcon") as key:
            value, _ = winreg.QueryValueEx(key, "")
            if value and Path(value).exists():
                logger.debug(f"Found xEdit at: {value}")
                return Path(value)
    except (OSError, ValueError) as e:
        logger.debug(f"Failed to find xEdit in registry: {e}")

    for name in ["FO4Edit64.exe", "xEdit64.exe", "FO4Edit.exe", "xEdit.exe"]:
        if Path(name).exists():
            logger.debug(f"Found xEdit in current directory: {name}")
            return Path(name).absolute()

    return None


def _find_fallout4_paths(winreg: type) -> tuple[Path | None, Path | None]:
    fallout4_path: Path | None = None
    ck_path: Path | None = None

    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\Bethesda Softworks\Fallout4") as key:
            install_path, _ = winreg.QueryValueEx(key, "installed path")
            if install_path:
                install_path: Path = Path(install_path)
                fo4_exe: Path = install_path / "Fallout4.exe"
                ck_exe: Path = install_path / "CreationKit.exe"

                if fo4_exe.exists():
                    fallout4_path = fo4_exe
                    logger.debug(f"Found Fallout 4 at: {fallout4_path}")

                if ck_exe.exists():
                    ck_path = ck_exe
                    logger.debug(f"Found Creation Kit at: {ck_path}")
    except (OSError, ValueError) as e:
        logger.debug(f"Failed to find Fallout 4 in registry: {e}")

    return fallout4_path, ck_path
