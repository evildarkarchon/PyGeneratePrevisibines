from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field, field_validator, model_validator

from PrevisLib.config.registry import find_tool_paths
from PrevisLib.models.data_classes import ArchiveTool, BuildMode, CKPEConfig, ToolPaths
from PrevisLib.utils.logging import get_logger

if TYPE_CHECKING:
    from loguru import Logger

logger: Logger = get_logger(__name__)


# noinspection PyNestedDecorators
class Settings(BaseModel):
    plugin_name: str = ""
    build_mode: BuildMode = BuildMode.CLEAN
    archive_tool: ArchiveTool = ArchiveTool.ARCHIVE2
    tool_paths: ToolPaths = Field(default_factory=ToolPaths)
    ckpe_config_path: Path | None = None
    ckpe_config: CKPEConfig | None = None
    working_directory: Path = Field(default_factory=Path.cwd)
    mo2_enabled: bool = False
    no_prompt: bool = False
    verbose: bool = False
    log_file: Path | None = None

    model_config = {"arbitrary_types_allowed": True}

    @field_validator("plugin_name")
    @classmethod
    def validate_plugin_name(cls, v: str) -> str:
        """
        Validates the provided plugin name to ensure it adheres to specific naming rules and
        does not conflict with reserved names. The function also verifies if the plugin name has
        an appropriate file extension and appends a default `.esp` extension if necessary.

        :param v: The plugin name string to validate.
        :type v: str
        :return: The validated and appropriately formatted plugin name.
        :rtype: str
        :raises ValueError: If the plugin name contains spaces, is a reserved name, or has an
            invalid file extension.
        """
        if not v:
            return v

        if " " in v:
            raise ValueError("Plugin name cannot contain spaces")

        reserved_names = {
            "Fallout4.esm",
            "DLCRobot.esm",
            "DLCworkshop01.esm",
            "DLCCoast.esm",
            "DLCworkshop02.esm",
            "DLCworkshop03.esm",
            "DLCNukaWorld.esm",
            "DLCUltraHighResolution.esm",
        }

        if v in reserved_names:
            raise ValueError(f"Cannot use reserved plugin name: {v}")

        # Check if it has a file extension
        path_obj = Path(v)
        if path_obj.suffix:
            # If it has an extension, it must be valid
            if not v.endswith((".esp", ".esm", ".esl")):
                raise ValueError(f"Invalid plugin extension '{path_obj.suffix}'. Must be .esp, .esm, or .esl")
        else:
            # If no extension, auto-append .esp
            v = f"{v}.esp"

        return v

    @field_validator("working_directory")
    @classmethod
    def validate_working_directory(cls, v: Any) -> Path:
        """
        Validates the 'working_directory' field to ensure it represents an existing
        path. Converts the value to a `Path` object if it is provided as a string,
        and raises a `ValueError` if the path does not exist.

        :param v: The value to validate, either as a string representing a path or
                  already as a `Path` object.
        :type v: Any
        :return: A `Path` object representing the validated working directory.
        :rtype: Path
        :raises ValueError: If the `working_directory` does not exist.
        """
        if isinstance(v, str):
            v = Path(v)
        if not v.exists():
            raise ValueError(f"Working directory does not exist: {v}")
        return v

    @model_validator(mode="after")
    def load_ckpe_config(self) -> Settings:
        """
        Validates and loads the CKPE configuration file. The method is triggered after the model validation phase.
        It checks the existence of the provided configuration file path, determines the file type based on its
        extension, and loads the contents using the appropriate parser. If the file does not exist or loading fails,
        the configuration is set to None. This method ensures the model's settings include appropriate CKPE config.

        :raises OSError: When there is an issue accessing the file system for CKPE config.
        :raises ValueError: When the CKPE config content is invalid or cannot be parsed for the given file type.
        :return: Current instance with the loaded CKPE configuration or set to None.
        :rtype: Settings
        """
        if self.ckpe_config_path and self.ckpe_config_path.exists():
            try:
                if self.ckpe_config_path.suffix == ".toml":
                    self.ckpe_config = CKPEConfig.from_toml(self.ckpe_config_path)
                else:
                    self.ckpe_config = CKPEConfig.from_ini(self.ckpe_config_path)
            except (OSError, ValueError) as e:
                logger.warning(f"Failed to load CKPE config: {e}")
        else:
            self.ckpe_config = None
        return self

    @classmethod
    def from_cli_args(  # noqa: PLR0913
        cls,
        plugin_name: str | None = None,
        build_mode: str | None = None,
        use_bsarch: bool = False,
        no_prompt: bool = False,
        verbose: bool = False,
        fallout4_path: Path | None = None,
        xedit_path: Path | None = None,
        bsarch_path: Path | None = None,
    ) -> Settings:
        """
        Creates and initializes a Settings instance based on the provided command-line
        arguments. This method configures the instance with paths and options tailored
        to the user's input and system environment. It also includes logic for automatic
        tool discovery for Windows platforms and ensures specified paths from the
        arguments are validated and applied.

        :param plugin_name: The name of the plugin to be used. If provided, disables
            interactive prompts unless overridden.
        :param build_mode: Specifies the mode for building plugins. Possible values
            are platform-dependent and case-insensitive.
        :param use_bsarch: If True, sets the archive tool preference to BSArch.
        :param no_prompt: If True, disables any interactive prompts.
        :param verbose: If True, enables verbose logging for debugging and detailed
            operation information.
        :param fallout4_path: Path to the installation folder of Fallout 4, which is
            used to configure related tools and paths automatically.
        :param xedit_path: Path to the xEdit executable, which identifies the location
            of xEdit tools and related utilities.
        :param bsarch_path: Path to the BSArch executable, overrides automatic discovery.
        :return: A configured Settings instance based on the provided values and system
            environment.
        """
        settings = cls()

        if plugin_name:
            settings.plugin_name = plugin_name
            settings.no_prompt = no_prompt or bool(plugin_name)

        if build_mode:
            settings.build_mode = BuildMode(build_mode.lower())

        if use_bsarch:
            settings.archive_tool = ArchiveTool.BSARCH

        settings.verbose = verbose

        # Start with automatic tool discovery if on Windows
        if sys.platform == "win32":
            settings.tool_paths = find_tool_paths()
        else:
            logger.warning("Running on non-Windows platform. Tool paths must be configured manually.")

        # Apply CLI path overrides
        if fallout4_path:
            # Override Fallout 4 installation path and derive related paths
            fallout4_exe: Path = fallout4_path / "Fallout4.exe"
            if fallout4_exe.exists():
                settings.tool_paths.fallout4 = fallout4_exe
                logger.debug(f"Using CLI-specified Fallout 4 path: {fallout4_exe}")

                # Derive Creation Kit path from Fallout 4 installation
                ck_exe: Path = fallout4_path / "CreationKit.exe"
                if ck_exe.exists():
                    settings.tool_paths.creation_kit = ck_exe
                    logger.debug(f"Found Creation Kit at Fallout 4 installation: {ck_exe}")
                else:
                    logger.warning(f"CreationKit.exe not found in Fallout 4 installation: {fallout4_path}")

                # Update archive tool paths based on new installation path
                archive_path: Path = fallout4_path / "Tools" / "Archive2" / "Archive2.exe"
                if archive_path.exists():
                    settings.tool_paths.archive2 = archive_path
                    logger.debug(f"Found Archive2 at Fallout 4 installation: {archive_path}")
            else:
                raise ValueError(f"Fallout4.exe not found in specified path: {fallout4_path}")

        if xedit_path:
            settings.tool_paths.xedit = xedit_path
            logger.debug(f"Using CLI-specified xEdit path: {xedit_path}")

            # Look for BSArch in the same directory as xEdit (only if not explicitly provided)
            if not bsarch_path:
                auto_bsarch_path: Path = xedit_path.parent / "BSArch.exe"
                if auto_bsarch_path.exists():
                    settings.tool_paths.bsarch = auto_bsarch_path
                    logger.debug(f"Found BSArch near xEdit: {auto_bsarch_path}")

        # Handle CLI-specified BSArch path
        if bsarch_path:
            settings.tool_paths.bsarch = bsarch_path
            logger.debug(f"Using CLI-specified BSArch path: {bsarch_path}")

        # Look for CKPE config files
        if settings.tool_paths.creation_kit is not None:
            ckpe_toml: Path = settings.tool_paths.creation_kit.parent / "CreationKitPlatformExtended.toml"
            ckpe_ini: Path = settings.tool_paths.creation_kit.parent / "CreationKitPlatformExtended.ini"

            if ckpe_toml.exists():
                settings.ckpe_config_path = ckpe_toml
            elif ckpe_ini.exists():
                settings.ckpe_config_path = ckpe_ini

        return settings

    def validate_tools(self) -> list[str]:
        return self.tool_paths.validate()
