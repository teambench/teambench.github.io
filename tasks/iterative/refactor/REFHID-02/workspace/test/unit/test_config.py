"""
6 unit tests for the YAML config loader.
These pass once src/config.py is migrated to use PyYAML.
"""
import os
import pytest
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.config import Config, reset_config

WORKSPACE = os.path.join(os.path.dirname(__file__), "..", "..")
YAML_CONFIG = os.path.join(WORKSPACE, "config", "app.yaml")


@pytest.fixture(autouse=True)
def reset():
    reset_config()
    yield
    reset_config()


@pytest.fixture
def cfg():
    return Config(YAML_CONFIG)


class TestYAMLConfig:
    def test_yaml_config_file_exists(self):
        """config/app.yaml must exist after migration."""
        assert os.path.exists(YAML_CONFIG), (
            f"config/app.yaml not found at {YAML_CONFIG}. "
            "Create it as part of the migration."
        )

    def test_database_host(self, cfg):
        """database.host must be 'localhost'."""
        assert cfg.get("database", "host") == "localhost"

    def test_database_port_as_int(self, cfg):
        """database.port must parse to integer 5432."""
        assert cfg.get_int("database", "port") == 5432

    def test_api_port(self, cfg):
        """api.port must be 8080."""
        assert cfg.get_int("api", "port") == 8080

    def test_api_debug_false(self, cfg):
        """api.debug must be False."""
        assert cfg.get_bool("api", "debug") is False

    def test_sections_present(self, cfg):
        """All four sections must be present: database, redis, api, logging."""
        sections = cfg.sections()
        for expected in ["database", "redis", "api", "logging"]:
            assert expected in sections, f"Missing section: {expected}"
