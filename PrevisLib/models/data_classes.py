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
