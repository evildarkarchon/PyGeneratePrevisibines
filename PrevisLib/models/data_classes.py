from __future__ import annotations

from configparser import ConfigParser, SectionProxy
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any


class BuildMode(Enum):
    CLEAN = "clean"
    FILTERED = "filtered"
    XBOX = "xbox"


class BuildStep(Enum):
    GENERATE_PRECOMBINED = auto()
    MERGE_COMBINED_OBJECTS = auto()
    ARCHIVE_MESHES = auto()
    COMPRESS_PSG = auto()
    BUILD_CDX = auto()
    GENERATE_PREVIS = auto()
    MERGE_PREVIS = auto()
    FINAL_PACKAGING = auto()

    def __str__(self) -> str:
        return self.name.replace("_", " ").title()


class BuildStatus(Enum):
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


class ArchiveTool(Enum):
    ARCHIVE2 = "Archive2"
    BSARCH = "BSArch"


@dataclass
class ToolPaths:
    creation_kit: Path | None = None
    xedit: Path | None = None
    archive2: Path | None = None
    bsarch: Path | None = None
    fallout4: Path | None = None

    def validate(self) -> list[str]:
        """
        Validates the configuration for required tools and files. Checks for the existence
        of necessary components such as Creation Kit, xEdit, Fallout 4, and archive tools.
        Additionally, validates xEdit scripts if xEdit is available. The method accumulates
        and returns a list of validation errors encountered during the process.

        :raises IOError: Raised internally during file validity checks in associated tools.

        :return: A list of error messages as strings describing each issue detected during the
            validation.
        :rtype: list[str]
        """
        from PrevisLib.utils.validation import validate_xedit_scripts

        errors: list[Any] = []
        if not self.creation_kit or not self.creation_kit.exists():
            errors.append("Creation Kit not found")
        if not self.xedit or not self.xedit.exists():
            errors.append("xEdit/FO4Edit not found")
        else:
            # Validate xEdit scripts if xEdit is found
            script_valid, script_message = validate_xedit_scripts(self.xedit)
            if not script_valid:
                errors.append(f"xEdit scripts validation failed: {script_message}")
        if not self.fallout4 or not self.fallout4.exists():
            errors.append("Fallout 4 not found")
        if not self.archive2 and not self.bsarch:
            errors.append("No archive tool found (Archive2 or BSArch)")
        return errors


@dataclass
class CKPEConfig:
    handle_setting: bool = True
    log_output_file: str = ""
    config_path: Path | None = None
    raw_config: dict[str, Any] = field(default_factory=dict)
    _from_factory: bool = field(default=False, init=True, repr=False)

    def __post_init__(self) -> None:
        if not self._from_factory:
            raise TypeError("CKPEConfig cannot be instantiated directly. Use CKPEConfig.from_toml() or CKPEConfig.from_ini() instead.")

    @classmethod
    def from_toml(cls, config_path: Path) -> CKPEConfig:
        """
        Creates an instance of the CKPEConfig class from a TOML configuration file.

        This class method reads the specified TOML configuration file, extracts the settings
        defined within, and initializes a CKPEConfig instance with these settings. It utilizes
        the `tomli` module to parse the TOML file. The method assumes the TOML structure includes
        sections such as 'CreationKit' and 'Log' with specific keys.

        :param config_path: The Path object representing the path to the TOML file.
        :type config_path: Path
        :return: A new instance of CKPEConfig configured with parameters extracted from the TOML
            file.
        :rtype: CKPEConfig
        """
        import tomli

        with config_path.open("rb") as f:
            data: dict[str, Any] = tomli.load(f)

        return cls(
            handle_setting=data.get("CreationKit", {}).get(
                "bBSPointerHandleExtremly", False
            ),  # Placeholder as CKPE release with TOML has not been released
            log_output_file=data.get("Log", {}).get("sOutputFile", ""),
            config_path=config_path,
            raw_config=data,
            _from_factory=True,
        )

    @classmethod
    def from_ini(cls, config_path: Path) -> CKPEConfig:
        """
        Creates an instance of CKPEConfig from an INI configuration file.

        This class method reads the specified INI file, parses its sections
        and keys, and initializes a CKPEConfig object with the parsed
        configuration values. The method ensures compatibility by checking
        for specific sections ('CreationKit' and 'Log') and retrieves only
        the necessary settings for initializing the instance.

        :param config_path: Path to the INI configuration file to be read.
        :type config_path: Path
        :return: An initialized CKPEConfig object with settings loaded from
                 the provided configuration file.
        :rtype: CKPEConfig
        """
        import configparser

        parser: ConfigParser = configparser.ConfigParser()
        parser.read(config_path)

        # Check for both CreationKit and Log sections
        ckpe_section: SectionProxy | dict[Any, Any] = parser["CreationKit"] if parser.has_section("CreationKit") else {}
        log_section: SectionProxy | dict[Any, Any] = parser["Log"] if parser.has_section("Log") else {}

        return cls(
            handle_setting=ckpe_section.getboolean("bBSPointerHandleExtremly", False)
            if isinstance(ckpe_section, SectionProxy)
            else ckpe_section.get("bBSPointerHandleExtremly", False),
            log_output_file=log_section.get("sOutputFile", "") if log_section else "",
            config_path=config_path,
            raw_config={s: dict(parser.items(s)) for s in parser.sections()},
            _from_factory=True,
        )


@dataclass
class BuildConfig:
    plugin_name: str
    build_mode: BuildMode = BuildMode.CLEAN
    archive_tool: ArchiveTool = ArchiveTool.ARCHIVE2
    tool_paths: ToolPaths = field(default_factory=ToolPaths)
    ckpe_config: CKPEConfig | None = None
    working_directory: Path = field(default_factory=Path.cwd)
    mo2_enabled: bool = False
    resume_from_step: BuildStep | None = None

    def __post_init__(self) -> None:
        if isinstance(self.working_directory, str):
            self.working_directory = Path(self.working_directory)
