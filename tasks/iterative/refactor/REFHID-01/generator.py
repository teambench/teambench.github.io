"""
Generator for REFHID-01: Service Extraction with Hidden Subscribers.
Parameterizes service names, field names, and subscriber behaviors from a seed.

Usage:
    python generator.py --seed 42 --output-dir ./generated/
"""
import argparse
import hashlib
import json
import os
import random
import shutil
import textwrap


AVATAR_FIELD_VARIANTS = ["avatar_url", "profile_picture", "photo_url", "headshot_url"]
BIO_FIELD_VARIANTS = ["bio", "about_me", "description", "summary"]
PREFS_FIELD_VARIANTS = ["preferences", "settings", "user_settings", "config"]
NAME_FIELD_VARIANTS = ["display_name", "full_name", "billing_name", "name"]

SERVICE_NAME_VARIANTS = ["ProfileService", "UserProfileService", "AccountProfileService"]
ENTITY_NAME_VARIANTS = ["UserProfile", "Profile", "AccountProfile"]

SUBSCRIBER_NAMES = [
    ("NotificationService", "notification"),
    ("AlertService", "alerts"),
    ("MessagingService", "messaging"),
]

EVENT_NAMES = [
    ("user.updated", "user.deleted"),
    ("account.updated", "account.deleted"),
    ("profile.updated", "profile.deleted"),
]


def seed_random(seed: int) -> random.Random:
    rng = random.Random()
    rng.seed(seed)
    return rng


def pick(rng: random.Random, lst: list):
    return lst[rng.randint(0, len(lst) - 1)]


def generate_params(seed: int) -> dict:
    rng = seed_random(seed)
    return {
        "seed": seed,
        "avatar_field": pick(rng, AVATAR_FIELD_VARIANTS),
        "bio_field": pick(rng, BIO_FIELD_VARIANTS),
        "prefs_field": pick(rng, PREFS_FIELD_VARIANTS),
        "name_field": pick(rng, NAME_FIELD_VARIANTS),
        "service_class": pick(rng, SERVICE_NAME_VARIANTS),
        "entity_class": pick(rng, ENTITY_NAME_VARIANTS),
        "update_event": pick(rng, EVENT_NAMES)[0],
        "delete_event": pick(rng, EVENT_NAMES)[1],
        "notif_subscriber": pick(rng, SUBSCRIBER_NAMES),
    }


def render_users_py(p: dict) -> str:
    return textwrap.dedent(f"""\
        \"\"\"User management monolith — {p['entity_class']} fields mixed in.\"\"\"
        from __future__ import annotations
        import uuid
        from datetime import datetime
        from typing import Optional, Dict, Any
        from monolith.events import dispatcher


        class {p['entity_class']}:
            def __init__(
                self,
                user_id: str,
                {p['avatar_field']}: str = "",
                {p['bio_field']}: str = "",
                {p['prefs_field']}: Optional[Dict[str, Any]] = None,
                {p['name_field']}: str = "",
            ):
                self.user_id = user_id
                self.{p['avatar_field']} = {p['avatar_field']}
                self.{p['bio_field']} = {p['bio_field']}
                self.{p['prefs_field']} = {p['prefs_field']} or {{}}
                self.{p['name_field']} = {p['name_field']}

            def to_dict(self) -> Dict[str, Any]:
                return {{
                    "user_id": self.user_id,
                    "{p['avatar_field']}": self.{p['avatar_field']},
                    "{p['bio_field']}": self.{p['bio_field']},
                    "{p['prefs_field']}": self.{p['prefs_field']},
                    "{p['name_field']}": self.{p['name_field']},
                }}


        class User:
            def __init__(
                self,
                email: str,
                {p['avatar_field']}: str = "",
                {p['bio_field']}: str = "",
                {p['prefs_field']}: Optional[Dict[str, Any]] = None,
                {p['name_field']}: str = "",
                user_id: Optional[str] = None,
            ):
                self.user_id: str = user_id or str(uuid.uuid4())
                self.email: str = email
                self.created_at: datetime = datetime.utcnow()
                self.{p['avatar_field']}: str = {p['avatar_field']}
                self.{p['bio_field']}: str = {p['bio_field']}
                self.{p['prefs_field']}: Dict[str, Any] = {p['prefs_field']} or {{}}
                self.{p['name_field']}: str = {p['name_field']}
                self.name: str = {p['name_field']}

            def update(self, **kwargs) -> None:
                for key, value in kwargs.items():
                    setattr(self, key, value)
                dispatcher.publish("{p['update_event']}", self)

            def delete(self) -> None:
                dispatcher.publish("{p['delete_event']}", self)
        """)


def render_profile_service_py(p: dict) -> str:
    return textwrap.dedent(f"""\
        \"\"\"
        {p['service_class']} — extracted from monolith.users.
        This is the SOLUTION file. In the task workspace it starts empty.
        \"\"\"
        from __future__ import annotations
        from typing import Optional, Dict, Any


        class {p['entity_class']}:
            def __init__(
                self,
                user_id: str,
                {p['avatar_field']}: str = "",
                {p['bio_field']}: str = "",
                {p['prefs_field']}: Optional[Dict[str, Any]] = None,
                {p['name_field']}: str = "",
            ):
                self.user_id = user_id
                self.{p['avatar_field']} = {p['avatar_field']}
                self.{p['bio_field']} = {p['bio_field']}
                self.{p['prefs_field']} = {p['prefs_field']} or {{}}
                self.{p['name_field']} = {p['name_field']}

            def to_dict(self) -> Dict[str, Any]:
                return {{
                    "user_id": self.user_id,
                    "{p['avatar_field']}": self.{p['avatar_field']},
                    "{p['bio_field']}": self.{p['bio_field']},
                    "{p['prefs_field']}": self.{p['prefs_field']},
                    "{p['name_field']}": self.{p['name_field']},
                }}


        class {p['service_class']}:
            def __init__(self):
                self._store: Dict[str, {p['entity_class']}] = {{}}

            def get_profile(self, user_id: str) -> Optional[{p['entity_class']}]:
                return self._store.get(user_id)

            def update_profile(self, user_id: str, **kwargs) -> {p['entity_class']}:
                profile = self._store.get(user_id) or {p['entity_class']}(user_id=user_id)
                for key, value in kwargs.items():
                    if hasattr(profile, key):
                        setattr(profile, key, value)
                self._store[user_id] = profile
                return profile

            def delete_profile(self, user_id: str) -> None:
                self._store.pop(user_id, None)
        """)


def generate(seed: int, output_dir: str) -> None:
    p = generate_params(seed)
    os.makedirs(output_dir, exist_ok=True)

    # Write params file
    with open(os.path.join(output_dir, "params.json"), "w") as f:
        json.dump(p, f, indent=2)

    # Write rendered files
    files = {
        "monolith_users.py": render_users_py(p),
        "profile_service_solution.py": render_profile_service_py(p),
    }
    for fname, content in files.items():
        path = os.path.join(output_dir, fname)
        with open(path, "w") as f:
            f.write(content)

    print(f"Generated REFHID-01 variant for seed={seed}")
    print(f"  avatar field:  {p['avatar_field']}")
    print(f"  bio field:     {p['bio_field']}")
    print(f"  prefs field:   {p['prefs_field']}")
    print(f"  name field:    {p['name_field']}")
    print(f"  service class: {p['service_class']}")
    print(f"  entity class:  {p['entity_class']}")
    print(f"  update event:  {p['update_event']}")
    print(f"  delete event:  {p['delete_event']}")
    print(f"Output: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Generate REFHID-01 task variants")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output-dir", default="./generated", help="Output directory")
    args = parser.parse_args()
    generate(args.seed, args.output_dir)


if __name__ == "__main__":
    main()
