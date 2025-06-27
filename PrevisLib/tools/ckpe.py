"""CKPE configuration handler for reading Creation Kit Platform Extended configs."""

from pathlib import Path

from loguru import logger

from PrevisLib.models.data_classes import CKPEConfig


class CKPEConfigHandler:
    """Handler for reading and parsing CKPE configuration files."""

    def __init__(self, fo4_path: Path) -> None:
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
        toml_path: Path = self.data_path / f"{plugin_name}_CKPEConfig.toml"
        if toml_path.exists():
            config: CKPEConfig | None = self._load_toml_config(toml_path)
            if config:
                return config

        # Try INI format (older)
        ini_path: Path = self.data_path / f"{plugin_name}_CKPEConfig.ini"
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
            config: CKPEConfig = CKPEConfig.from_toml(config_path)
            logger.success(f"Loaded TOML CKPE configuration from {config_path}")

        except (OSError, ValueError) as e:
            logger.error(f"Failed to load TOML config {config_path}: {e}")
            return None
        else:
            return config

    def _load_ini_config(self, config_path: Path) -> CKPEConfig | None:
        """Load CKPE configuration from INI file.

        Args:
            config_path: Path to the INI config file

        Returns:
            CKPEConfig if valid, None otherwise
        """
        try:
            config: CKPEConfig = CKPEConfig.from_ini(config_path)
            logger.success(f"Loaded INI CKPE configuration from {config_path}")

        except (OSError, ValueError) as e:
            logger.error(f"Failed to load INI config {config_path}: {e}")
            return None
        else:
            return config
