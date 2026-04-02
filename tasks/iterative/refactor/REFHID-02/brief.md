# REFHID-02: Migrate Config from INI to YAML

## Your Task

Migrate the application configuration from `config/app.ini` to `config/app.yaml`. Update `src/config.py` to use PyYAML instead of configparser. All 10 tests must pass.

## Files to Work With

```
workspace/
  config/app.ini          # Current INI config — migrate this
  src/config.py           # Config loader — switch to PyYAML
  deploy/start.sh         # Startup script
  deploy/health_check.sh  # Health check script
  docker-compose.yml      # Docker compose
  test/unit/test_config.py         # 6 unit tests
  test/integration/test_deploy.py  # 4 integration tests
  requirements.txt        # Install with pip install -r requirements.txt
```

## Quick Start

```bash
cd workspace
pip install -r requirements.txt
python -m pytest test/ -v
```

## What to Change

1. Create `config/app.yaml` with the same values as `config/app.ini`
2. Update `src/config.py` to load from YAML using `import yaml`
3. Keep the same public API: `Config.get(section, key)` and `Config.get_int(section, key)`

## Note

Check deploy scripts in `deploy/` for any config references — they may also need updating.

## Target

```
python -m pytest test/ -v
# 10 passed
```
