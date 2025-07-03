"""CKPE configuration handler for reading Creation Kit Platform Extended configs."""

from pathlib import Path

from loguru import logger

from PrevisLib.models.data_classes import CKPEConfig


class CKPEConfigHandler:
    """Handler for reading and parsing CKPE configuration files."""

    def __init__(self, fo4_path: Path) -> None:
        self.fo4_path = fo4_path
        # Handle different path scenarios
        if fo4_path.name.lower() == "fallout4.exe":
            self.data_path = fo4_path.parent / "Data"
        elif fo4_path.name.lower() == "data":
            self.data_path = fo4_path
        else:
            self.data_path = fo4_path / "Data"

    def load_config(self, plugin_name: str) -> CKPEConfig | None:
        """
        Loads the CKPE configuration for a given plugin. This method attempts to find and load the
        configuration file for the specified plugin in either TOML or INI format. The TOML format
        is attempted first as it is considered the newer format. If a valid configuration is not
        found in TOML format, the INI format is attempted. If neither format is found or valid,
        the method logs the absence of the configuration and returns None.

        :param plugin_name: The name of the plugin for which to load the configuration.
        :type plugin_name: str
        :return: A CKPEConfig object if a valid configuration is found, otherwise None.
        :rtype: CKPEConfig | None
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
        """
        Loads a TOML configuration file and converts it into a CKPEConfig object. If the
        configuration file cannot be loaded or parsed, logs the error and returns None.

        :param config_path: The path to the TOML configuration file.
        :type config_path: Path
        :return: A CKPEConfig object representing the loaded configuration, or None
            if the file could not be loaded or parsed.
        :rtype: CKPEConfig | None
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
        """
        Loads configuration from an INI file and creates a CKPEConfig object. This
        method attempts to parse the specified INI file and, if successful, loads
        the configuration into a CKPEConfig instance. If the file cannot be read or
        parsed due to an OSError or ValueError, it logs an error message and returns
        None.

        :param config_path: Path to the INI configuration file
        :type config_path: Path
        :return: A CKPEConfig object if successful, otherwise None
        :rtype: CKPEConfig | None
        """
        try:
            config: CKPEConfig = CKPEConfig.from_ini(config_path)
            logger.success(f"Loaded INI CKPE configuration from {config_path}")

        except (OSError, ValueError) as e:
            logger.error(f"Failed to load INI config {config_path}: {e}")
            return None
        else:
            return config
