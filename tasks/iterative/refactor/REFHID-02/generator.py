"""
Generator for REFHID-02: Config Format Migration.
Parameterizes section names, key names, and values from a seed.

Usage:
    python generator.py --seed 42 --output-dir ./generated/
"""
import argparse
import json
import os
import random
import textwrap

DB_NAME_VARIANTS = ["myapp_db", "appdb", "production_db", "service_db"]
DB_USER_VARIANTS = ["appuser", "dbadmin", "service_account", "api_user"]
APP_PORT_VARIANTS = [8080, 8000, 3000, 5000, 8888]
REDIS_DB_VARIANTS = [0, 1, 2]
LOG_LEVEL_VARIANTS = ["INFO", "DEBUG", "WARNING"]
LOG_FORMAT_VARIANTS = ["json", "text", "structured"]

SECTION_NAME_MAP_VARIANTS = [
    {"database": "database", "redis": "redis", "api": "api", "logging": "logging"},
    {"database": "db", "redis": "cache", "api": "server", "logging": "log"},
    {"database": "postgres", "redis": "redis", "api": "http", "logging": "logger"},
]


def seed_random(seed: int) -> random.Random:
    rng = random.Random()
    rng.seed(seed)
    return rng


def pick(rng, lst):
    return lst[rng.randint(0, len(lst) - 1)]


def generate_params(seed: int) -> dict:
    rng = seed_random(seed)
    sections = pick(rng, SECTION_NAME_MAP_VARIANTS)
    return {
        "seed": seed,
        "db_name": pick(rng, DB_NAME_VARIANTS),
        "db_user": pick(rng, DB_USER_VARIANTS),
        "app_port": pick(rng, APP_PORT_VARIANTS),
        "redis_db": pick(rng, REDIS_DB_VARIANTS),
        "log_level": pick(rng, LOG_LEVEL_VARIANTS),
        "log_format": pick(rng, LOG_FORMAT_VARIANTS),
        "sections": sections,
    }


def render_ini(p: dict) -> str:
    s = p["sections"]
    return textwrap.dedent(f"""\
        [{s['database']}]
        host = localhost
        port = 5432
        name = {p['db_name']}
        user = {p['db_user']}
        password = s3cr3t

        [{s['redis']}]
        host = localhost
        port = 6379
        db = {p['redis_db']}
        password =

        [{s['api']}]
        host = 0.0.0.0
        port = {p['app_port']}
        debug = false
        secret_key = change-me-in-production
        workers = 4

        [{s['logging']}]
        level = {p['log_level']}
        format = {p['log_format']}
        output = stdout
        """)


def render_yaml_solution(p: dict) -> str:
    s = p["sections"]
    return textwrap.dedent(f"""\
        {s['database']}:
          host: localhost
          port: 5432
          name: {p['db_name']}
          user: {p['db_user']}
          password: s3cr3t

        {s['redis']}:
          host: localhost
          port: 6379
          db: {p['redis_db']}
          password: ""

        {s['api']}:
          host: "0.0.0.0"
          port: {p['app_port']}
          debug: false
          secret_key: change-me-in-production
          workers: 4

        {s['logging']}:
          level: {p['log_level']}
          format: {p['log_format']}
          output: stdout
        """)


def generate(seed: int, output_dir: str) -> None:
    p = generate_params(seed)
    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, "params.json"), "w") as f:
        json.dump(p, f, indent=2)

    with open(os.path.join(output_dir, "app.ini"), "w") as f:
        f.write(render_ini(p))

    with open(os.path.join(output_dir, "app.yaml.solution"), "w") as f:
        f.write(render_yaml_solution(p))

    print(f"Generated REFHID-02 variant for seed={seed}")
    print(f"  db_name:  {p['db_name']}")
    print(f"  app_port: {p['app_port']}")
    print(f"  sections: {p['sections']}")
    print(f"Output: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Generate REFHID-02 task variants")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", default="./generated")
    args = parser.parse_args()
    generate(args.seed, args.output_dir)


if __name__ == "__main__":
    main()
