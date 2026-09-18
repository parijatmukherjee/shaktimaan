from __future__ import annotations

import dataclasses
from pathlib import Path

import yaml

CONFIG_FIELDS = (
    "project_name",
    "requirements_file",
    "feature_tracker_file",
    "requirements_status_file",
    "git_user_name",
    "git_user_email",
)


class ConfigError(Exception):
    """Raised when .shaktimaan/config.yml is missing or malformed."""


@dataclasses.dataclass
class ShaktimaanConfig:
    project_name: str
    requirements_file: str
    feature_tracker_file: str
    requirements_status_file: str
    git_user_name: str
    git_user_email: str


def save_config(config: ShaktimaanConfig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {field: getattr(config, field) for field in CONFIG_FIELDS}
    path.write_text(yaml.safe_dump(data, sort_keys=False))


def load_config(path: Path) -> ShaktimaanConfig:
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")

    raw = yaml.safe_load(path.read_text()) or {}

    missing = [field for field in CONFIG_FIELDS if field not in raw]
    if missing:
        raise ConfigError(
            f"Config file {path} is missing required key(s): {', '.join(missing)}"
        )

    return ShaktimaanConfig(**{field: raw[field] for field in CONFIG_FIELDS})
