# REFHID-02: Config Format Migration (INI → YAML)

## Overview

Migrate the application configuration from INI format (`config/app.ini`) to YAML format (`config/app.yaml`). Update all code that reads the config. All 10 tests must pass and the service must start cleanly.

This is a **multi-turn** task. Round 1 migrates the Python config loader. Round 2 requires fixing deploy scripts and docker-compose that still parse the INI file directly.

## What to Migrate

### Python side
- `config/app.ini` → `config/app.yaml`
- `src/config.py` — switch from `configparser` to `PyYAML`
- Keep identical key structure (sections become top-level YAML keys)

### INI → YAML mapping
```ini
[database]
host = localhost
port = 5432
name = myapp
```
becomes:
```yaml
database:
  host: localhost
  port: 5432
  name: myapp
```

## Hidden Constraints (Shell/Docker layer)

These are **not mentioned in the Executor's brief**. The Planner knows them. They cause round-1 failures when the Verifier runs deploy integration tests.

### 1. `deploy/start.sh` parses INI directly
```bash
DB_HOST=$(grep "^host" config/app.ini | cut -d= -f2 | tr -d ' ')
APP_PORT=$(grep "^port" config/app.ini | cut -d= -f2 | tr -d ' ')
```
Must be rewritten to use a Python helper or `python3 -c` to read the YAML.

### 2. `deploy/health_check.sh` parses INI directly
```bash
PORT=$(awk -F= '/^port/{print $2}' config/app.ini | tr -d ' ')
```
Must be rewritten similarly.

### 3. `docker-compose.yml` mounts `config/app.ini`
```yaml
volumes:
  - ./config/app.ini:/app/config/app.ini:ro
```
Must be changed to mount `config/app.yaml`.

## Fix Required (Round 2)

1. Rewrite `deploy/start.sh` to read config from `config/app.yaml` (use `python3 -c "import yaml; ..."` or a helper script)
2. Rewrite `deploy/health_check.sh` similarly
3. Update `docker-compose.yml` volume mount to use `config/app.yaml`

## Success Criterion

All 10 tests pass:
- 6 unit tests in `test/unit/test_config.py`
- 4 integration tests in `test/integration/test_deploy.py`

```bash
cd workspace && python -m pytest test/ -v
```

Score = passing_tests / 10

## Constraints

- `config/app.ini` may be removed or kept (tests don't require it after migration)
- `config/app.yaml` must exist and be valid YAML
- `src/config.py` must use `yaml` (PyYAML) — not `configparser`
- Shell scripts must source config from YAML (not INI)
- Python 3.9+, PyYAML required

## Files

| File | Role | Modify? |
|------|------|---------|
| `config/app.ini` | Old INI config | Remove or keep |
| `config/app.yaml` | New YAML config (create) | Create |
| `src/config.py` | Config loader | Yes — switch to PyYAML |
| `deploy/start.sh` | Shell startup script | Yes (round 2) |
| `deploy/health_check.sh` | Shell health check | Yes (round 2) |
| `docker-compose.yml` | Docker compose | Yes (round 2) |
| `test/unit/test_config.py` | 6 unit tests | No |
| `test/integration/test_deploy.py` | 4 deploy integration tests | No |

## Evaluation

```
Score = passing_tests / 10
```

- Round 1 oracle: ~0.55 (Python tests pass, deploy tests fail)
- Round 2 expected: 1.0 (all 10 pass)
