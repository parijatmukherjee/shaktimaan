from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Callable

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


FIELD_PROMPTS = {
    "project_name": "Project name",
    "requirements_file": "Path to the requirements file",
    "feature_tracker_file": "Path to the feature-tracker file",
    "requirements_status_file": "Path to the requirements-status file",
    "git_user_name": "Git commit identity: user.name",
    "git_user_email": "Git commit identity: user.email",
}

FIELD_DEFAULTS = {
    "project_name": "",
    "requirements_file": "requirements/requirements.md",
    "feature_tracker_file": "requirements/feature-tracker.md",
    "requirements_status_file": "docs/REQUIREMENTS-STATUS.md",
    "git_user_name": "",
    "git_user_email": "",
}


def collect_config(
    overrides: dict[str, str],
    prompt_fn: Callable[[str, str], str],
    defaults: dict[str, str] | None = None,
) -> ShaktimaanConfig:
    field_defaults = defaults if defaults is not None else FIELD_DEFAULTS
    values: dict[str, str] = {}
    for field in CONFIG_FIELDS:
        if field in overrides:
            values[field] = overrides[field]
        else:
            values[field] = prompt_fn(field, field_defaults[field])
    return ShaktimaanConfig(**values)
