# REFHID-02: Config Format Migration (INI → YAML)

## Description

Migrate the application config from `config/app.ini` (configparser) to `config/app.yaml` (PyYAML). The hidden constraint: `deploy/start.sh` and `deploy/health_check.sh` parse the INI file directly with grep/awk, and `docker-compose.yml` mounts `app.ini`. These shell-layer issues only surface when the Verifier runs deploy integration tests.

## Multi-Turn Dynamics

| Round | What happens |
|-------|-------------|
| Round 1 | Executor migrates `src/config.py` to PyYAML. Unit tests pass (6/10). Deploy integration tests fail — shell scripts and docker-compose still reference `app.ini`. |
| Round 2 | Verifier's attestation flags the 4 failing deploy tests. Executor updates shell scripts and docker-compose. All 10 pass. |

The integration tests fail in round 1 because:
- `test_start_sh_succeeds_without_ini` — hides `app.ini`, `start.sh` exits with error
- `test_start_sh_outputs_correct_port` — `start.sh` can't parse YAML
- `test_health_check_succeeds_without_ini` — `health_check.sh` exits with error
- `test_docker_compose_uses_yaml_volume` — finds `app.ini` in docker-compose.yml

## Expected Scores

| Agent type | Expected score |
|-----------|---------------|
| Oracle (reads spec.md) | 0.55 round 1 → 1.0 round 2 |
| Single-pass (brief.md only) | ~0.65 |
| Multi-turn | 1.0 |

## Stopping Condition

Stop when score = 1.0 (all 10 tests pass), or after 3 rounds.

## Running Tests

```bash
cd workspace
pip install -r requirements.txt
python -m pytest test/ -v
```

## Grading

```bash
bash grader.sh
# outputs: 0.0000 to 1.0000
```

Score = passing_tests / 10

## Generating Variants

```bash
python generator.py --seed 123 --output-dir ./generated/seed-123/
```

Parameterizes: section names, DB name, app port, redis DB, log level, log format.

## Real-World Provenance

This task is inspired by **docker/compose#9362** — a real config format migration that broke shell scripts and Docker Compose volume mounts that had been parsing the old format directly:
https://github.com/docker/compose/issues/9362

The issue documents a real migration scenario: the application layer was updated correctly, but `grep`/`awk`-based shell consumers in CI pipelines and deploy tooling still referenced the old format, causing failures that only surfaced during deploy integration tests — not unit tests. This task recreates that exact failure mode with `deploy/start.sh`, `deploy/health_check.sh`, and the `docker-compose.yml` volume mount.

See [`../PROVENANCE.md`](../PROVENANCE.md) for full details.
