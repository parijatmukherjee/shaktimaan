from __future__ import annotations

import shutil
from importlib import resources
from pathlib import Path

from shaktimaan.config import ShaktimaanConfig, save_config


def _presets_root() -> Path:
    return Path(str(resources.files("shaktimaan"))) / "presets"


def install_presets(target_dir: Path, config: ShaktimaanConfig) -> None:
    presets = _presets_root()

    skills_dir = target_dir / ".claude" / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    for command_dir in sorted((presets / "core").iterdir()):
        dest = skills_dir / command_dir.name
        shutil.copytree(command_dir, dest, dirs_exist_ok=True)

    shaktimaan_dir = target_dir / ".shaktimaan"
    shaktimaan_dir.mkdir(parents=True, exist_ok=True)

    shutil.copytree(
        presets / "scripts", shaktimaan_dir / "scripts", dirs_exist_ok=True
    )
    shutil.copytree(
        presets / "templates", shaktimaan_dir / "templates", dirs_exist_ok=True
    )
    shutil.copy2(
        presets / "scaffolding" / "extensions.yml",
        shaktimaan_dir / "extensions.yml",
    )

    save_config(config, shaktimaan_dir / "config.yml")
