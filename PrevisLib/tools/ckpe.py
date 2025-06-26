"""CKPE configuration handler for reading Creation Kit Platform Extended configs."""

import configparser
from pathlib import Path

import tomli
from loguru import logger

from ..models.data_classes import CKPEConfig


class CKPEConfigHandler:
    """Handler for reading and parsing CKPE configuration files."""
    
    def __init__(self, fo4_path: Path):
        self.fo4_path = fo4_path
        self.data_path = fo4_path / "Data"
        
    def load_config(self, plugin_name: str) -> CKPEConfig | None:
        """Load CKPE configuration for a plugin.
        
        Args:
            plugin_name: Name of the plugin (without extension)
            
        Returns:
            CKPEConfig if found and valid, None otherwise
        """
        # Try TOML format first (newer)
        toml_path = self.data_path / f"{plugin_name}_CKPEConfig.toml"
        if toml_path.exists():
            config = self._load_toml_config(toml_path)
            if config:
                return config
                
        # Try INI format (older)
        ini_path = self.data_path / f"{plugin_name}_CKPEConfig.ini"
        if ini_path.exists():
            config = self._load_ini_config(ini_path)
            if config:
                return config
                
        logger.info(f"No CKPE configuration found for {plugin_name}")
        return None
        
    def _load_toml_config(self, config_path: Path) -> CKPEConfig | None:
        """Load CKPE configuration from TOML file.
        
        Args:
            config_path: Path to the TOML config file
            
        Returns:
            CKPEConfig if valid, None otherwise
        """
        try:
            with open(config_path, 'rb') as f:
                data = tomli.load(f)
                
            # Extract previs settings
            previs_data = data.get('Previs', {})
            
            config = CKPEConfig(
                enabled=previs_data.get('bEnabled', True),
                cell_size_x=previs_data.get('iCellSizeX', 4096),
                cell_size_y=previs_data.get('iCellSizeY', 4096),
                max_triangles=previs_data.get('iMaxTriangles', 30000),
                min_triangles=previs_data.get('iMinTriangles', 30),
                max_size=previs_data.get('fMaxSize', 2048.0),
                min_size=previs_data.get('fMinSize', 32.0),
                exclusion_list=previs_data.get('ExclusionList', []),
                inclusion_list=previs_data.get('InclusionList', [])
            )
            
            logger.success(f"Loaded TOML CKPE configuration from {config_path}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load TOML config {config_path}: {e}")
            return None
            
    def _load_ini_config(self, config_path: Path) -> CKPEConfig | None:
        """Load CKPE configuration from INI file.
        
        Args:
            config_path: Path to the INI config file
            
        Returns:
            CKPEConfig if valid, None otherwise
        """
        try:
            parser = configparser.ConfigParser()
            parser.read(config_path)
            
            if 'Previs' not in parser:
                logger.warning(f"No [Previs] section in {config_path}")
                return None
                
            previs = parser['Previs']
            
            # Parse lists
            exclusion_list = self._parse_ini_list(previs.get('ExclusionList', ''))
            inclusion_list = self._parse_ini_list(previs.get('InclusionList', ''))
            
            config = CKPEConfig(
                enabled=previs.getboolean('bEnabled', True),
                cell_size_x=previs.getint('iCellSizeX', 4096),
                cell_size_y=previs.getint('iCellSizeY', 4096),
                max_triangles=previs.getint('iMaxTriangles', 30000),
                min_triangles=previs.getint('iMinTriangles', 30),
                max_size=previs.getfloat('fMaxSize', 2048.0),
                min_size=previs.getfloat('fMinSize', 32.0),
                exclusion_list=exclusion_list,
                inclusion_list=inclusion_list
            )
            
            logger.success(f"Loaded INI CKPE configuration from {config_path}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load INI config {config_path}: {e}")
            return None
            
    def _parse_ini_list(self, value: str) -> list[str]:
        """Parse a comma-separated list from INI value.
        
        Args:
            value: Comma-separated string
            
        Returns:
            List of trimmed values
        """
        if not value:
            return []
            
        return [item.strip() for item in value.split(',') if item.strip()]
        
    def create_default_config(self, plugin_name: str, format: str = "toml") -> bool:
        """Create a default CKPE configuration file.
        
        Args:
            plugin_name: Name of the plugin (without extension)
            format: Config format ("toml" or "ini")
            
        Returns:
            True if created successfully
        """
        default_config = CKPEConfig()
        
        if format == "toml":
            config_path = self.data_path / f"{plugin_name}_CKPEConfig.toml"
            content = self._generate_toml_content(default_config)
        else:
            config_path = self.data_path / f"{plugin_name}_CKPEConfig.ini"
            content = self._generate_ini_content(default_config)
            
        try:
            with open(config_path, 'w') as f:
                f.write(content)
            logger.success(f"Created default CKPE config at {config_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create CKPE config: {e}")
            return False
            
    def _generate_toml_content(self, config: CKPEConfig) -> str:
        """Generate TOML content from CKPEConfig.
        
        Args:
            config: CKPEConfig instance
            
        Returns:
            TOML formatted string
        """
        content = f"""# CKPE Configuration for Previs Generation

[Previs]
# Enable previs generation
bEnabled = {str(config.enabled).lower()}

# Cell grid size
iCellSizeX = {config.cell_size_x}
iCellSizeY = {config.cell_size_y}

# Triangle count limits
iMaxTriangles = {config.max_triangles}
iMinTriangles = {config.min_triangles}

# Object size limits
fMaxSize = {config.max_size}
fMinSize = {config.min_size}

# Exclusion list (cells to skip)
ExclusionList = {config.exclusion_list}

# Inclusion list (cells to force include)
InclusionList = {config.inclusion_list}
"""
        return content
        
    def _generate_ini_content(self, config: CKPEConfig) -> str:
        """Generate INI content from CKPEConfig.
        
        Args:
            config: CKPEConfig instance
            
        Returns:
            INI formatted string
        """
        exclusion_str = ','.join(config.exclusion_list) if config.exclusion_list else ''
        inclusion_str = ','.join(config.inclusion_list) if config.inclusion_list else ''
        
        content = f"""; CKPE Configuration for Previs Generation

[Previs]
; Enable previs generation
bEnabled={config.enabled}

; Cell grid size
iCellSizeX={config.cell_size_x}
iCellSizeY={config.cell_size_y}

; Triangle count limits
iMaxTriangles={config.max_triangles}
iMinTriangles={config.min_triangles}

; Object size limits
fMaxSize={config.max_size}
fMinSize={config.min_size}

; Exclusion list (cells to skip)
ExclusionList={exclusion_str}

; Inclusion list (cells to force include)  
InclusionList={inclusion_str}
"""
        return content