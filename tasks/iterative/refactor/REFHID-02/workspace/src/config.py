"""
Application configuration loader.
Currently uses configparser to read INI format.
TODO: Migrate to PyYAML to read config/app.yaml
"""
import configparser
import os
from typing import Optional

# Path to config file — relative to workspace root
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "app.ini")


class Config:
    """
    Reads application configuration from INI file.
    Public API:
      - Config.get(section, key) -> str
      - Config.get_int(section, key) -> int
      - Config.get_bool(section, key) -> bool
      - Config.sections() -> list[str]
    """

    def __init__(self, config_path: Optional[str] = None):
        self._path = config_path or CONFIG_PATH
        self._parser = configparser.ConfigParser()
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self._path):
            raise FileNotFoundError(f"Config file not found: {self._path}")
        self._parser.read(self._path)

    def get(self, section: str, key: str) -> str:
        """Return a string config value."""
        return self._parser.get(section, key)

    def get_int(self, section: str, key: str) -> int:
        """Return an integer config value."""
        return self._parser.getint(section, key)

    def get_bool(self, section: str, key: str) -> bool:
        """Return a boolean config value."""
        return self._parser.getboolean(section, key)

    def sections(self) -> list:
        """Return list of section names."""
        return self._parser.sections()

    def as_dict(self) -> dict:
        """Return full config as a nested dict."""
        return {
            section: dict(self._parser[section])
            for section in self._parser.sections()
        }


# Module-level singleton
_config: Optional[Config] = None


def get_config(config_path: Optional[str] = None) -> Config:
    """Get or create the module-level config singleton."""
    global _config
    if _config is None:
        _config = Config(config_path)
    return _config


def reset_config() -> None:
    """Reset the singleton (useful for testing)."""
    global _config
    _config = None
