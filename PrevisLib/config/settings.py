from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from PrevisLib.config.registry import find_tool_paths
from PrevisLib.models.data_classes import ArchiveTool, BuildMode, CKPEConfig, ToolPaths
from PrevisLib.utils.logging import get_logger

logger = get_logger(__name__)


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
        if not v:
            return v
            
        if " " in v:
            raise ValueError("Plugin name cannot contain spaces")
        
        reserved_names = {
            "Fallout4.esm", "DLCRobot.esm", "DLCworkshop01.esm", 
            "DLCCoast.esm", "DLCworkshop02.esm", "DLCworkshop03.esm",
            "DLCNukaWorld.esm", "DLCUltraHighResolution.esm"
        }
        
        if v in reserved_names:
            raise ValueError(f"Cannot use reserved plugin name: {v}")
        
        if not v.endswith((".esp", ".esm", ".esl")):
            v = f"{v}.esp"
            
        return v
    
    @field_validator("working_directory")
    @classmethod
    def validate_working_directory(cls, v: Any) -> Path:
        if isinstance(v, str):
            v = Path(v)
        if not v.exists():
            raise ValueError(f"Working directory does not exist: {v}")
        return v
    
    @model_validator(mode="after")
    def load_ckpe_config(self) -> Settings:
        if self.ckpe_config_path and self.ckpe_config_path.exists():
            try:
                if self.ckpe_config_path.suffix == ".toml":
                    self.ckpe_config = CKPEConfig.from_toml(self.ckpe_config_path)
                else:
                    self.ckpe_config = CKPEConfig.from_ini(self.ckpe_config_path)
            except Exception as e:
                logger.warning(f"Failed to load CKPE config: {e}")
        else:
            self.ckpe_config = None
        return self
    
    @classmethod
    def from_cli_args(
        cls,
        plugin_name: str | None = None,
        build_mode: str | None = None,
        use_bsarch: bool = False,
        no_prompt: bool = False,
        verbose: bool = False,
    ) -> Settings:
        settings = cls()
        
        if plugin_name:
            settings.plugin_name = plugin_name
            settings.no_prompt = no_prompt or bool(plugin_name)
        
        if build_mode:
            settings.build_mode = BuildMode(build_mode.lower())
        
        if use_bsarch:
            settings.archive_tool = ArchiveTool.BSARCH
        
        settings.verbose = verbose
        
        if sys.platform == "win32":
            settings.tool_paths = find_tool_paths()
        else:
            logger.warning("Running on non-Windows platform. Tool paths must be configured manually.")
        
        ckpe_toml = settings.working_directory / "CreationKitPlatformExtended.toml"
        ckpe_ini = settings.working_directory / "CreationKitPlatformExtended.ini"
        
        if ckpe_toml.exists():
            settings.ckpe_config_path = ckpe_toml
        elif ckpe_ini.exists():
            settings.ckpe_config_path = ckpe_ini
        
        return settings
    
    def validate_tools(self) -> list[str]:
        return self.tool_paths.validate()