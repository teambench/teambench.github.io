"""
4 integration tests that simulate running deploy scripts and checking docker-compose.
These tests will FAIL in round 1 if deploy scripts and docker-compose still reference app.ini.
They pass once start.sh, health_check.sh, and docker-compose.yml are updated for YAML.
"""
import os
import subprocess
import pytest

WORKSPACE = os.path.join(os.path.dirname(__file__), "..", "..")
DEPLOY_DIR = os.path.join(WORKSPACE, "deploy")
START_SH = os.path.join(DEPLOY_DIR, "start.sh")
HEALTH_SH = os.path.join(DEPLOY_DIR, "health_check.sh")
COMPOSE_FILE = os.path.join(WORKSPACE, "docker-compose.yml")
YAML_CONFIG = os.path.join(WORKSPACE, "config", "app.yaml")
INI_CONFIG = os.path.join(WORKSPACE, "config", "app.ini")


class TestStartScript:
    def test_start_sh_succeeds_without_ini(self):
        """
        start.sh must work when app.ini does NOT exist.
        If start.sh still greps app.ini it will fail when INI is removed/absent.
        We simulate post-migration by temporarily hiding the INI file.
        """
        # Hide INI if it exists to simulate migration completion
        ini_hidden = INI_CONFIG + ".hidden"
        ini_existed = os.path.exists(INI_CONFIG)
        if ini_existed:
            os.rename(INI_CONFIG, ini_hidden)

        try:
            result = subprocess.run(
                ["bash", START_SH],
                capture_output=True,
                text=True,
                cwd=WORKSPACE,
            )
            assert result.returncode == 0, (
                f"start.sh failed (exit {result.returncode}).\n"
                f"stdout: {result.stdout}\n"
                f"stderr: {result.stderr}\n"
                "start.sh must be updated to read config/app.yaml instead of app.ini."
            )
            assert "START_OK=true" in result.stdout, (
                "start.sh must output START_OK=true"
            )
        finally:
            if ini_existed:
                os.rename(ini_hidden, INI_CONFIG)

    def test_start_sh_outputs_correct_port(self):
        """start.sh must output APP_PORT=8080 (from api.port in YAML config)."""
        ini_hidden = INI_CONFIG + ".hidden"
        ini_existed = os.path.exists(INI_CONFIG)
        if ini_existed:
            os.rename(INI_CONFIG, ini_hidden)
        try:
            result = subprocess.run(
                ["bash", START_SH],
                capture_output=True,
                text=True,
                cwd=WORKSPACE,
            )
            assert "APP_PORT=8080" in result.stdout, (
                f"start.sh must output APP_PORT=8080. Got:\n{result.stdout}"
            )
        finally:
            if ini_existed:
                os.rename(ini_hidden, INI_CONFIG)


class TestHealthCheckScript:
    def test_health_check_succeeds_without_ini(self):
        """
        health_check.sh must work when app.ini does NOT exist.
        If it still uses awk on app.ini it will fail.
        """
        ini_hidden = INI_CONFIG + ".hidden"
        ini_existed = os.path.exists(INI_CONFIG)
        if ini_existed:
            os.rename(INI_CONFIG, ini_hidden)
        try:
            result = subprocess.run(
                ["bash", HEALTH_SH],
                capture_output=True,
                text=True,
                cwd=WORKSPACE,
            )
            assert result.returncode == 0, (
                f"health_check.sh failed (exit {result.returncode}).\n"
                f"stdout: {result.stdout}\n"
                f"stderr: {result.stderr}\n"
                "health_check.sh must be updated to read config/app.yaml."
            )
            assert "HEALTH_OK=true" in result.stdout
        finally:
            if ini_existed:
                os.rename(ini_hidden, INI_CONFIG)


class TestDockerCompose:
    def test_docker_compose_uses_yaml_volume(self):
        """
        docker-compose.yml must mount config/app.yaml, not config/app.ini.
        """
        assert os.path.exists(COMPOSE_FILE), "docker-compose.yml not found"
        with open(COMPOSE_FILE) as f:
            content = f.read()

        assert "app.yaml" in content, (
            "docker-compose.yml must mount config/app.yaml (not app.ini). "
            "Update the volumes section to: ./config/app.yaml:/app/config/app.yaml:ro"
        )
        # Ensure the old INI reference is gone
        assert "app.ini" not in content, (
            "docker-compose.yml still references app.ini — remove it."
        )
