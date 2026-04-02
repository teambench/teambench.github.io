"""
Application configuration loader.
Currently uses configparser to read INI format.
TODO: Migrate to PyYAML to read config/app.yaml
"""
import configparser
import os
from typing import Optional

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "app.ini")

class Config:
    def __init__(self, config_path: Optional[str] = None):
        self._path = config_path or CONFIG_PATH
        self._parser = configparser.ConfigParser()
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self._path):
            raise FileNotFoundError(f"Config file not found: {self._path}")
        self._parser.read(self._path)

    def get(self, section: str, key: str) -> str:
        return self._parser.get(section, key)

    def get_int(self, section: str, key: str) -> int:
        return self._parser.getint(section, key)

    def get_bool(self, section: str, key: str) -> bool:
        return self._parser.getboolean(section, key)

    def sections(self) -> list:
        return self._parser.sections()

    def as_dict(self) -> dict:
        return {section: dict(self._parser[section]) for section in self._parser.sections()}

_config: Optional[Config] = None

def get_config(config_path: Optional[str] = None) -> Config:
    global _config
    if _config is None:
        _config = Config(config_path)
    return _config

def reset_config() -> None:
    global _config
    _config = None
