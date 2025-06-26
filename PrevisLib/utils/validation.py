from __future__ import annotations

from pathlib import Path

from PrevisLib.utils.logging import get_logger

logger = get_logger(__name__)


RESERVED_PLUGIN_NAMES = {
    "Fallout4.esm",
    "DLCRobot.esm",
    "DLCworkshop01.esm",
    "DLCCoast.esm",
    "DLCworkshop02.esm",
    "DLCworkshop03.esm",
    "DLCNukaWorld.esm",
    "DLCUltraHighResolution.esm",
}

VALID_PLUGIN_EXTENSIONS = {".esp", ".esm", ".esl"}


def validate_plugin_name(plugin_name: str) -> tuple[bool, str]:
    if not plugin_name:
        return False, "Plugin name cannot be empty"
    
    if " " in plugin_name:
        return False, "Plugin name cannot contain spaces"
    
    plugin_path = Path(plugin_name)
    
    if plugin_path.suffix not in VALID_PLUGIN_EXTENSIONS:
        return False, f"Plugin must have valid extension: {', '.join(VALID_PLUGIN_EXTENSIONS)}"
    
    if plugin_name in RESERVED_PLUGIN_NAMES:
        return False, f"Cannot use reserved plugin name: {plugin_name}"
    
    return True, ""


def validate_tool_path(tool_path: Path | None, tool_name: str) -> tuple[bool, str]:
    if not tool_path:
        return False, f"{tool_name} path not specified"
    
    if not tool_path.exists():
        return False, f"{tool_name} not found at: {tool_path}"
    
    if not tool_path.is_file():
        return False, f"{tool_name} path is not a file: {tool_path}"
    
    if tool_path.suffix.lower() != ".exe":
        return False, f"{tool_name} must be an executable (.exe): {tool_path}"
    
    return True, ""


def validate_directory(directory: Path, name: str, must_exist: bool = True) -> tuple[bool, str]:
    if must_exist and not directory.exists():
        return False, f"{name} directory does not exist: {directory}"
    
    if directory.exists() and not directory.is_dir():
        return False, f"{name} path is not a directory: {directory}"
    
    return True, ""


def check_tool_version(tool_path: Path, expected_version: str | None = None) -> tuple[bool, str]:
    if not tool_path.exists():
        return False, "Tool not found"
    
    return True, "Version check not implemented"


def validate_ckpe_config(config_path: Path) -> tuple[bool, str]:
    if not config_path.exists():
        return False, f"CKPE config not found: {config_path}"
    
    if config_path.suffix not in {".toml", ".ini"}:
        return False, f"CKPE config must be .toml or .ini: {config_path}"
    
    try:
        if config_path.suffix == ".toml":
            import tomli
            with open(config_path, "rb") as f:
                tomli.load(f)
        else:
            import configparser
            parser = configparser.ConfigParser()
            parser.read(config_path)
    except Exception as e:
        return False, f"Failed to parse CKPE config: {e}"
    
    return True, ""


def validate_archive_format(archive_path: Path) -> tuple[bool, str]:
    if not archive_path.exists():
        return False, f"Archive not found: {archive_path}"
    
    if archive_path.suffix.lower() != ".ba2":
        return False, f"Archive must be .ba2 format: {archive_path}"
    
    return True, ""