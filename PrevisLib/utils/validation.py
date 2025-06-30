from __future__ import annotations

import configparser
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any

from PrevisLib.utils.logging import get_logger

if TYPE_CHECKING:
    from loguru import Logger
    from pefile import PE

logger: Logger = get_logger(__name__)


RESERVED_PLUGIN_NAMES: set[str] = {
    "Fallout4.esm",
    "DLCRobot.esm",
    "DLCworkshop01.esm",
    "DLCCoast.esm",
    "DLCworkshop02.esm",
    "DLCworkshop03.esm",
    "DLCNukaWorld.esm",
    "DLCUltraHighResolution.esm",
}

VALID_PLUGIN_EXTENSIONS: set[str] = {".esp", ".esm", ".esl"}

# Required xEdit scripts with their minimum versions
REQUIRED_XEDIT_SCRIPTS: dict[str, str] = {
    "Batch_FO4MergePrevisandCleanRefr.pas": "V2.2",
    "Batch_FO4MergeCombinedObjectsAndCheck.pas": "V1.5",
}


def validate_plugin_name(plugin_name: str) -> tuple[bool, str]:
    """
    Validates the provided plugin name based on several criteria such as non-emptiness, absence
    of spaces, valid extension, and it not being a reserved name. Returns a tuple indicating
    whether the validation was successful and an error message if it was not.

    :param plugin_name: The name of the plugin to validate.
    :type plugin_name: str
    :return: A tuple where the first element is a boolean indicating whether the validation
        passed, and the second element is the error message if validation failed.
    :rtype: tuple[bool, str]
    """
    if not plugin_name:
        return False, "Plugin name cannot be empty"

    if " " in plugin_name:
        return False, "Plugin name cannot contain spaces"

    plugin_path: Path = Path(plugin_name)

    if plugin_path.suffix.lower() not in VALID_PLUGIN_EXTENSIONS:
        return False, f"Plugin must have valid extension: {', '.join(VALID_PLUGIN_EXTENSIONS)}"

    if plugin_name in RESERVED_PLUGIN_NAMES:
        return False, f"Cannot use reserved plugin name: {plugin_name}"

    return True, ""


def validate_xedit_scripts(xedit_path: Path) -> tuple[bool, str]:
    """
    Validates that the required xEdit scripts are present and have the correct versions.

    This function checks the existence of xEdit scripts and verifies their versions
    against predefined values. It scans the "Edit Scripts" directory located in the
    same directory as the provided xEdit executable and validates the scripts based
    on the requirements specified in `REQUIRED_XEDIT_SCRIPTS`. Any missing or
    outdated scripts are logged and reported in the returned tuple.

    :param xedit_path: Path to the xEdit executable file.
    :type xedit_path: Path
    :return: A tuple containing a boolean indicating validation success and a
        message describing the result. If validation fails, the message includes
        details about which scripts are missing or have version mismatches.
    :rtype: tuple[bool, str]
    """
    if not xedit_path or not xedit_path.exists():
        return False, "xEdit path not found"

    # Get the directory containing xEdit executable
    xedit_dir: Path = xedit_path.parent
    scripts_dir: Path = xedit_dir / "Edit Scripts"

    # Check if Edit Scripts directory exists
    if not scripts_dir.exists():
        return False, f"Edit Scripts directory not found at: {scripts_dir}"

    missing_scripts: list[str] = []
    version_mismatches: list[str] = []

    for script_name, required_version in REQUIRED_XEDIT_SCRIPTS.items():
        script_path: Path = scripts_dir / script_name

        # Check if script exists
        if not script_path.exists():
            missing_scripts.append(script_name)
            logger.error(f"Required xEdit script missing: {script_name}")
            continue

        # Check script version
        try:
            with script_path.open(encoding="utf-8", errors="ignore") as f:
                content: str = f.read()

            # Search for version string (case-insensitive, like the batch file)
            if required_version.upper() not in content.upper():
                version_mismatches.append(f"{script_name} (found old version, {required_version} required)")
                logger.error(f"Old script {script_name} found, {required_version} required")
            else:
                logger.debug(f"Script {script_name} version {required_version} validated")

        except (OSError, UnicodeDecodeError) as e:
            logger.error(f"Failed to read script {script_name}: {e}")
            missing_scripts.append(f"{script_name} (read error)")

    # Build error message if any issues found
    if missing_scripts or version_mismatches:
        error_parts: list[str] = []
        if missing_scripts:
            error_parts.append(f"Missing scripts: {', '.join(missing_scripts)}")
        if version_mismatches:
            error_parts.append(f"Version mismatches: {', '.join(version_mismatches)}")

        return False, "; ".join(error_parts)

    logger.info("All required xEdit scripts validated successfully")
    return True, "All required xEdit scripts found with correct versions"


def create_plugin_from_template(data_path: Path, target_plugin_name: str) -> tuple[bool, str]:
    """
    Creates a plugin file in the specified data directory from a predefined template. The method
    ensures that the plugin file follows specific requirements, such as uniqueness and required file
    formats, and performs various validation checks. It also handles cases where Mod Organizer 2
    (MO2) is used, ensuring proper file copying and availability.

    :param data_path: The path to the directory containing the template and managing plugins.
    :type data_path: Path
    :param target_plugin_name: The desired name of the new plugin file. If no extension is
                               provided, '.esp' will automatically be appended.
    :type target_plugin_name: str
    :return: A tuple where the first element is a boolean indicating success or failure, and
             the second element is a message providing details of the result.
    :rtype: tuple[bool, str]
    """
    from PrevisLib.utils.file_system import mo2_aware_copy, wait_for_output_file

    # Auto-append .esp if no extension provided
    plugin_path: Path = Path(target_plugin_name)
    if not plugin_path.suffix:
        target_plugin_name = f"{target_plugin_name}.esp"
        logger.debug(f"No extension provided, appended .esp: {target_plugin_name}")

    template_path: Path = data_path / "xPrevisPatch.esp"
    target_path: Path = data_path / target_plugin_name

    # Check if template exists
    if not template_path.exists():
        return False, "xPrevisPatch.esp template not found in Data directory"

    # Check if target already exists
    if target_path.exists():
        return False, f"Plugin {target_plugin_name} already exists"

    # Check if target plugin would have an existing archive (matches batch file logic)
    plugin_base: str = Path(target_plugin_name).stem
    archive_path: Path = data_path / f"{plugin_base} - Main.ba2"
    if archive_path.exists():
        return False, f"Plugin already has an archive: {archive_path.name}"

    try:
        logger.info(f"Creating plugin {target_plugin_name} from xPrevisPatch.esp template")

        # Copy template to target location with MO2-aware handling
        mo2_aware_copy(template_path, target_path, delay=2.0)

        # Wait for the file to be available (important for MO2)
        if not wait_for_output_file(target_path, timeout=10.0, check_interval=1.0):
            return False, f"Failed to create {target_plugin_name} - file not accessible after copy"

        logger.success(f"Successfully created {target_plugin_name} from template")
        return True, f"Created {target_plugin_name} from xPrevisPatch.esp template"  # noqa: TRY300

    except (OSError, shutil.Error, Exception) as e:
        logger.error(f"Failed to copy template: {e}")
        return False, f"Failed to copy template: {e}"


def validate_tool_path(tool_path: Path | None, tool_name: str) -> tuple[bool, str]:
    """
    Validates the given path to ensure it points to an executable file for a specified
    tool. This function verifies multiple conditions including the existence of the
    path, whether it is a file, and whether it has the correct `.exe` extension.

    :param tool_path: The path to the tool to be validated. It should point to a file
        with the `.exe` extension. Accepts None when the tool path is not specified.
    :type tool_path: Path | None
    :param tool_name: The name of the tool for which the path is being validated.
    :type tool_name: str
    :return: A tuple containing a boolean to indicate if the validation succeeded
        and a string providing the validation result or an error message.
    :rtype: tuple[bool, str]
    """
    if not tool_path:
        return False, f"{tool_name} path not specified"

    if not tool_path.exists():
        return False, f"{tool_name} not found at: {tool_path}"

    if tool_path.is_dir():
        return False, f"{tool_name} path is not a file (it's a directory): {tool_path}"

    if not tool_path.is_file():
        return False, f"{tool_name} not found at: {tool_path}"

    if tool_path.suffix.lower() != ".exe":
        return False, f"{tool_name} must be an executable (.exe): {tool_path}"

    return True, f"{tool_name} found and validated"


def validate_directory(directory: Path, name: str, must_exist: bool = True) -> tuple[bool, str]:
    """
    Validates whether a given directory exists and is a valid directory path based
    on the provided parameters. This function ensures that if a directory is
    required to exist, it does exist and is indeed a directory.

    :param directory: A Path object representing the directory to validate.
    :param name: A string representing the name of the directory for identification
        purposes in error messages.
    :param must_exist: A boolean flag indicating whether the directory is required
        to exist. Defaults to True.
    :return: A tuple where the first element is a boolean indicating the validation
        result, and the second element is a string message detailing validation
        errors or an empty string if validation succeeds.
    """
    if must_exist and not directory.exists():
        return False, f"{name} directory does not exist: {directory}"

    if directory.exists() and not directory.is_dir():
        return False, f"{name} path is not a directory: {directory}"

    return True, ""


def check_tool_version(tool_path: Path, expected_version: str | None = None) -> tuple[bool, str]:
    """
    Checks the specified executable file for version information and compares it
    with the expected version, if provided. The function is designed to handle
    Windows PE (Portable Executable) files and utilizes the `pefile` library
    to extract version details embedded in the file. If the `pefile` library
    is not available, the check is skipped unless an expected version is
    specified. For non-Windows executables, a note is returned indicating
    that the version check was skipped.

    :param tool_path: Path to the executable file to check.
    :param expected_version: The version string to compare against, or None if no
       comparison is needed.
    :return: A tuple containing a boolean indicating success or failure, and a
       string message describing the outcome.
    """
    if not tool_path.exists():
        return False, "Tool not found"

    try:
        import pefile
    except ImportError:
        return True, "pefile not available - version check skipped"

    pe: PE | None = None
    try:
        pe = pefile.PE(str(tool_path))

        # Look for version info in the file
        if hasattr(pe, "VS_VERSIONINFO"):
            for file_info in pe.FileInfo[0]:
                if file_info.Key.decode() == "StringFileInfo":
                    for string_table in file_info.StringTable:
                        for entry in string_table.entries.items():
                            key: Any = entry[0].decode()
                            value: Any = entry[1].decode()
                            if key in ("FileVersion", "ProductVersion"):
                                version: Any = value.strip()
                                if expected_version:
                                    if version == expected_version:
                                        return True, f"Version matches: {version}"
                                    return False, f"Version mismatch: found {version}, expected {expected_version}"
                                return True, f"Version: {version}"

        # If no version info found
        if expected_version:
            return False, "No version information found in executable"
        return True, "No version information available"  # noqa: TRY300

    except (OSError, ValueError, AttributeError) as e:
        return False, f"Failed to read executable version: {e}"
    except pefile.PEFormatError:
        # Handle non-PE files (e.g., Linux executables) gracefully
        return True, "Not a Windows executable - version check skipped"
    finally:
        if pe is not None:
            pe.close()


def validate_ckpe_config(config_path: Path) -> tuple[bool, str]:
    """
    Validates the CKPE configuration file provided in the specified path. The function ensures
    the file exists, verifies the file extension to be `.toml` or `.ini`, and attempts
    to parse the configuration using the appropriate format. Returns a boolean to indicate
    the validation result and an optional error message in case validation fails.

    :param config_path: Path to the CKPE configuration file to validate.
    :type config_path: Path
    :return: A tuple where the first value is a boolean indicating success or failure,
             and the second value is a string containing error details if validation fails.
    :rtype: tuple[bool, str]
    """
    if not config_path.exists():
        return False, f"CKPE config not found: {config_path}"

    if config_path.suffix not in {".toml", ".ini"}:
        return False, f"CKPE config must be .toml or .ini: {config_path}"

    try:
        if config_path.suffix == ".toml":
            import tomli

            with config_path.open("rb") as f:
                tomli.load(f)
        else:
            parser: configparser.ConfigParser = configparser.ConfigParser()
            parser.read(config_path)
    except (OSError, ImportError, ValueError, KeyError) as e:
        return False, f"Failed to parse CKPE config: {e}"
    except configparser.Error as e:
        return False, f"Failed to parse CKPE config: {e}"

    return True, ""


def validate_archive_format(archive_path: Path) -> tuple[bool, str]:
    """
    Validates the format of a specified archive file to ensure it meets the expected
    criteria of existence and proper file extension.

    :param archive_path: The path to the archive file to validate
    :type archive_path: Path
    :return: A tuple containing a boolean indicating whether the archive is
        valid, and a string message providing additional information or the
        reason for failure
    :rtype: tuple[bool, str]
    """
    if not archive_path.exists():
        return False, f"Archive not found: {archive_path}"

    if archive_path.suffix.lower() != ".ba2":
        return False, f"Archive must be .ba2 format: {archive_path}"

    return True, ""
