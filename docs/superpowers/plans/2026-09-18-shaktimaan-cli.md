# Shaktimaan CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `shaktimaan init [DIR]` — a Python CLI, installable via `uv tool install`, that scaffolds a 17-command spec-driven-development workflow (as Claude Code skills) into any target project, with all project-specific paths/identity resolved from a per-project config file rather than hardcoded.

**Architecture:** A `presets/` directory inside the package holds static, generic Markdown skill files, bash helper scripts, and Markdown templates. `shaktimaan init` prompts for a small config (or takes flags), writes it to `<target>/.shaktimaan/config.yml`, and copies the preset tree verbatim into `<target>/.claude/skills/` and `<target>/.shaktimaan/`. No template-rendering/placeholder-substitution step exists — every installed skill reads `.shaktimaan/config.yml` at run time for the paths/identity it needs, so changing a path later is a one-line config edit, not a reinstall.

**Tech Stack:** Python ≥3.11, `typer` (CLI framework), `pyyaml` (config + extensions.yml), `pytest` + `typer.testing.CliRunner` for tests, packaged with `pyproject.toml` (hatchling build backend), installed via `uv tool install`.

**Spec:** `docs/superpowers/specs/2026-09-18-shaktimaan-cli-design.md`

## Global Constraints

- No AI agent other than Claude Code is supported in v1 — every preset path is `.claude/skills/...`, no per-agent branching.
- No template placeholder substitution (`{{TOKEN}}`) anywhere — config values are read at runtime by the installed skills, never baked into rendered files. This overrides an earlier draft of the design that mentioned a templating engine; the design doc's own stated rationale ("changing a path later is a one-line config edit, not a re-render") only holds under the runtime-lookup approach, so that's what this plan implements.
- `shaktimaan init` is the only CLI command in v1. Do not add `upgrade`/`check`.
- No project-specific names (e.g. any prior private project this workflow was drawn from) appear anywhere in committed files — presets, docs, or code. Only the repo owner's name appears, in LICENSE and package metadata.
- Every git commit in this repo uses only the local git identity already configured (`Parijat Mukherjee <parijat_mukherjee@live.com>`) with no `Co-Authored-By` or "Generated with Claude Code" trailer.
- PyPI publishing is out of scope — `uv tool install` from a local/git checkout is enough for v1.

---

### Task 1: Project scaffolding — package skeleton and CLI entry point

**Files:**
- Create: `pyproject.toml`
- Create: `src/shaktimaan/__init__.py`
- Create: `src/shaktimaan/cli.py`
- Create: `tests/test_cli.py`
- Create: `.gitignore`

**Interfaces:**
- Produces: `shaktimaan.cli.app` — a `typer.Typer()` instance; `shaktimaan.cli.main()` — the console-script entry point calling `app()`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_cli.py
from typer.testing import CliRunner

from shaktimaan.cli import app

runner = CliRunner()


def test_version_flag_prints_version_and_exits_zero():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "shaktimaan" in result.stdout.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cli.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'shaktimaan'` (package doesn't exist yet).

- [ ] **Step 3: Create `pyproject.toml`**

```toml
[project]
name = "shaktimaan-cli"
version = "0.1.0"
description = "A personal Spec-Driven Development (SDD) CLI toolkit for Claude Code."
readme = "README.md"
license = { file = "LICENSE" }
authors = [{ name = "Parijat Mukherjee" }]
requires-python = ">=3.11"
dependencies = [
    "typer>=0.12",
    "pyyaml>=6.0",
]

[project.scripts]
shaktimaan = "shaktimaan.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/shaktimaan"]

[dependency-groups]
dev = [
    "pytest>=8.0",
]
```

- [ ] **Step 4: Create `src/shaktimaan/__init__.py`**

```python
__version__ = "0.1.0"
```

- [ ] **Step 5: Create `src/shaktimaan/cli.py`**

```python
import typer

from shaktimaan import __version__

app = typer.Typer(
    name="shaktimaan",
    help="A personal Spec-Driven Development (SDD) CLI toolkit for Claude Code.",
    no_args_is_help=True,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"shaktimaan {__version__}")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show the shaktimaan version and exit.",
    ),
) -> None:
    """Shaktimaan: scaffold a spec-driven-development workflow into your project."""


def main() -> None:
    app()
```

- [ ] **Step 6: Create `.gitignore`**

```
__pycache__/
*.pyc
.venv/
dist/
*.egg-info/
.pytest_cache/
```

- [ ] **Step 7: Run test to verify it passes**

Run: `uv run pytest tests/test_cli.py -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml src/shaktimaan/__init__.py src/shaktimaan/cli.py tests/test_cli.py .gitignore
git commit -m "Scaffold shaktimaan CLI package with a --version smoke test"
```

---

### Task 2: Config model — load/save `.shaktimaan/config.yml`

**Files:**
- Create: `src/shaktimaan/config.py`
- Create: `tests/test_config.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `shaktimaan.config.ShaktimaanConfig` (dataclass: `project_name: str`, `requirements_file: str`, `feature_tracker_file: str`, `requirements_status_file: str`, `git_user_name: str`, `git_user_email: str`); `shaktimaan.config.load_config(path: pathlib.Path) -> ShaktimaanConfig`; `shaktimaan.config.save_config(config: ShaktimaanConfig, path: pathlib.Path) -> None`; `shaktimaan.config.ConfigError(Exception)`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_config.py
import pytest

from shaktimaan.config import ConfigError, ShaktimaanConfig, load_config, save_config

SAMPLE = ShaktimaanConfig(
    project_name="Example",
    requirements_file="requirements/requirements.md",
    feature_tracker_file="requirements/feature-tracker.md",
    requirements_status_file="docs/REQUIREMENTS-STATUS.md",
    git_user_name="Ada Lovelace",
    git_user_email="ada@example.com",
)


def test_save_then_load_round_trips(tmp_path):
    path = tmp_path / "config.yml"
    save_config(SAMPLE, path)

    loaded = load_config(path)

    assert loaded == SAMPLE


def test_load_missing_file_raises_config_error(tmp_path):
    with pytest.raises(ConfigError, match="not found"):
        load_config(tmp_path / "does-not-exist.yml")


def test_load_missing_key_raises_config_error(tmp_path):
    path = tmp_path / "config.yml"
    path.write_text("project_name: Example\n")

    with pytest.raises(ConfigError, match="requirements_file"):
        load_config(path)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'shaktimaan.config'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/shaktimaan/config.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_config.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/shaktimaan/config.py tests/test_config.py
git commit -m "Add ShaktimaanConfig load/save with round-trip and error-path tests"
```

---

### Task 3: Interactive + non-interactive config collection

**Files:**
- Modify: `src/shaktimaan/config.py`
- Modify: `tests/test_config.py`

**Interfaces:**
- Consumes: `ShaktimaanConfig` (Task 2).
- Produces: `shaktimaan.config.collect_config(overrides: dict[str, str], prompt_fn: Callable[[str, str], str]) -> ShaktimaanConfig` — `overrides` holds any values already supplied (e.g. via CLI flags); `prompt_fn(field_name, default) -> str` is called for every field not present in `overrides`, so tests can inject a fake without touching stdin.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_config.py
from shaktimaan.config import collect_config

DEFAULTS = {
    "project_name": "MyProject",
    "requirements_file": "requirements/requirements.md",
    "feature_tracker_file": "requirements/feature-tracker.md",
    "requirements_status_file": "docs/REQUIREMENTS-STATUS.md",
    "git_user_name": "",
    "git_user_email": "",
}


def test_collect_config_prompts_for_every_missing_field():
    prompted_fields = []

    def fake_prompt(field_name: str, default: str) -> str:
        prompted_fields.append(field_name)
        return DEFAULTS[field_name] or "placeholder"

    config = collect_config(overrides={}, prompt_fn=fake_prompt)

    assert set(prompted_fields) == {
        "project_name",
        "requirements_file",
        "feature_tracker_file",
        "requirements_status_file",
        "git_user_name",
        "git_user_email",
    }
    assert config.project_name == "MyProject"


def test_collect_config_skips_prompting_for_overridden_fields():
    prompted_fields = []

    def fake_prompt(field_name: str, default: str) -> str:
        prompted_fields.append(field_name)
        return "should-not-be-used"

    config = collect_config(
        overrides={"project_name": "FromFlag", **{k: v for k, v in DEFAULTS.items() if k != "project_name"}},
        prompt_fn=fake_prompt,
    )

    assert prompted_fields == []
    assert config.project_name == "FromFlag"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_config.py -v`
Expected: FAIL — `ImportError: cannot import name 'collect_config'`

- [ ] **Step 3: Write minimal implementation**

Append to `src/shaktimaan/config.py`:

```python
from typing import Callable

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
) -> ShaktimaanConfig:
    values: dict[str, str] = {}
    for field in CONFIG_FIELDS:
        if field in overrides and overrides[field]:
            values[field] = overrides[field]
        else:
            values[field] = prompt_fn(field, FIELD_DEFAULTS[field])
    return ShaktimaanConfig(**values)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_config.py -v`
Expected: PASS (4 tests total in this file)

- [ ] **Step 5: Commit**

```bash
git add src/shaktimaan/config.py tests/test_config.py
git commit -m "Add collect_config with injectable prompt function for CLI/flag/test use"
```

---

### Task 4: Port the static bash scripts and Markdown templates

These six scripts and five templates are generic Spec-Driven-Development plumbing (feature numbering, prerequisite checks, template resolution) with no project-specific content — they only need their internal `.specify` references renamed to `.shaktimaan`. This task is a mechanical, scripted port from whatever local source checkout you're drawing from (a prior project with a `.specify/` directory populated by spec-kit) — set `SOURCE_REPO` to that checkout's path. Nothing under `SOURCE_REPO` or its contents is committed; only the rewritten output is.

**Files:**
- Create: `src/shaktimaan/presets/scripts/bash/check-prerequisites.sh`
- Create: `src/shaktimaan/presets/scripts/bash/common.sh`
- Create: `src/shaktimaan/presets/scripts/bash/create-new-feature.sh`
- Create: `src/shaktimaan/presets/scripts/bash/resolve-template.sh`
- Create: `src/shaktimaan/presets/scripts/bash/setup-plan.sh`
- Create: `src/shaktimaan/presets/scripts/bash/setup-tasks.sh`
- Create: `src/shaktimaan/presets/templates/checklist-template.md`
- Create: `src/shaktimaan/presets/templates/constitution-template.md`
- Create: `src/shaktimaan/presets/templates/plan-template.md`
- Create: `src/shaktimaan/presets/templates/spec-template.md`
- Create: `src/shaktimaan/presets/templates/tasks-template.md`
- Create: `tests/test_presets_static.py`

**Interfaces:**
- Produces: on-disk preset files under `src/shaktimaan/presets/scripts/bash/` and `src/shaktimaan/presets/templates/`, consumed by Task 6's `install_presets`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_presets_static.py
from pathlib import Path

PRESETS = Path(__file__).parent.parent / "src" / "shaktimaan" / "presets"

SCRIPTS = [
    "check-prerequisites.sh",
    "common.sh",
    "create-new-feature.sh",
    "resolve-template.sh",
    "setup-plan.sh",
    "setup-tasks.sh",
]

TEMPLATES = [
    "checklist-template.md",
    "constitution-template.md",
    "plan-template.md",
    "spec-template.md",
    "tasks-template.md",
]


def test_all_static_scripts_exist_and_are_executable():
    for name in SCRIPTS:
        path = PRESETS / "scripts" / "bash" / name
        assert path.exists(), f"missing {path}"
        assert path.stat().st_mode & 0o111, f"{path} is not executable"


def test_all_static_templates_exist():
    for name in TEMPLATES:
        assert (PRESETS / "templates" / name).exists()


def test_no_leftover_specify_references_in_scripts():
    for name in SCRIPTS:
        text = (PRESETS / "scripts" / "bash" / name).read_text()
        assert ".specify" not in text, f"{name} still references .specify"
        assert "Spec Kit" not in text, f"{name} still says 'Spec Kit'"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_presets_static.py -v`
Expected: FAIL — files don't exist yet.

- [ ] **Step 3: Run the port script**

```bash
SOURCE_REPO="/path/to/your/local/checkout/with/.specify"   # <- set this
mkdir -p src/shaktimaan/presets/scripts/bash src/shaktimaan/presets/templates

for f in check-prerequisites.sh common.sh create-new-feature.sh resolve-template.sh setup-plan.sh setup-tasks.sh; do
  sed \
    -e 's/\.specify/\.shaktimaan/g' \
    -e 's/SPECIFY_INIT_DIR/SHAKTIMAAN_INIT_DIR/g' \
    -e 's/Spec Kit/Shaktimaan/g' \
    -e 's/spec-kit/shaktimaan/g' \
    "$SOURCE_REPO/.specify/scripts/bash/$f" > "src/shaktimaan/presets/scripts/bash/$f"
  chmod +x "src/shaktimaan/presets/scripts/bash/$f"
done

for f in checklist-template.md constitution-template.md plan-template.md spec-template.md tasks-template.md; do
  cp "$SOURCE_REPO/.specify/templates/$f" "src/shaktimaan/presets/templates/$f"
done
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_presets_static.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/shaktimaan/presets/scripts src/shaktimaan/presets/templates tests/test_presets_static.py
git commit -m "Port static SDD scripts and templates, renamed off .specify"
```

---

### Task 5: Port the 10 spec-kit-shaped command skills

These 10 command templates (`specify`, `clarify`, `plan`, `tasks`, `analyze`, `checklist`, `implement`, `converge`, `taskstoissues`, `constitution`) contain no project-specific paths in their bodies — they only reference `.specify/` (spec-kit's own scaffolding directory) and each other by name. This task renames both, plus strips the `metadata.author: github-spec-kit` / `metadata.source` frontmatter fields (no longer accurate once renamed) and updates each `compatibility` line. Same `SOURCE_REPO` convention as Task 4.

**Files:**
- Create: `src/shaktimaan/presets/core/specify-shaktimaan/SKILL.md`
- Create: `src/shaktimaan/presets/core/clarify-shaktimaan/SKILL.md`
- Create: `src/shaktimaan/presets/core/plan-shaktimaan/SKILL.md`
- Create: `src/shaktimaan/presets/core/tasks-shaktimaan/SKILL.md`
- Create: `src/shaktimaan/presets/core/analyze-shaktimaan/SKILL.md`
- Create: `src/shaktimaan/presets/core/checklist-shaktimaan/SKILL.md`
- Create: `src/shaktimaan/presets/core/implement-shaktimaan/SKILL.md`
- Create: `src/shaktimaan/presets/core/converge-shaktimaan/SKILL.md`
- Create: `src/shaktimaan/presets/core/taskstoissues-shaktimaan/SKILL.md`
- Create: `src/shaktimaan/presets/core/constitution-shaktimaan/SKILL.md`
- Create: `tests/test_presets_core_speckit.py`

**Interfaces:**
- Produces: 10 skill directories under `src/shaktimaan/presets/core/`, consumed by Task 8's `install_presets`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_presets_core_speckit.py
from pathlib import Path

CORE = Path(__file__).parent.parent / "src" / "shaktimaan" / "presets" / "core"

RENAMED = [
    "specify-shaktimaan",
    "clarify-shaktimaan",
    "plan-shaktimaan",
    "tasks-shaktimaan",
    "analyze-shaktimaan",
    "checklist-shaktimaan",
    "implement-shaktimaan",
    "converge-shaktimaan",
    "taskstoissues-shaktimaan",
    "constitution-shaktimaan",
]


def test_each_command_has_a_skill_file_with_matching_name():
    for name in RENAMED:
        skill_file = CORE / name / "SKILL.md"
        assert skill_file.exists(), f"missing {skill_file}"
        text = skill_file.read_text()
        assert f'name: "{name}"' in text
        assert "github-spec-kit" not in text
        assert ".specify" not in text
        for other in RENAMED:
            # every internal cross-reference must use the new name, not "speckit-"
            assert f"/speckit-{other.removesuffix('-shaktimaan')}" not in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_presets_core_speckit.py -v`
Expected: FAIL — files don't exist yet.

- [ ] **Step 3: Run the port script**

```bash
SOURCE_REPO="/path/to/your/local/checkout/with/.claude/skills"   # <- set this

declare -A RENAME=(
  [speckit-specify]=specify-shaktimaan
  [speckit-clarify]=clarify-shaktimaan
  [speckit-plan]=plan-shaktimaan
  [speckit-tasks]=tasks-shaktimaan
  [speckit-analyze]=analyze-shaktimaan
  [speckit-checklist]=checklist-shaktimaan
  [speckit-implement]=implement-shaktimaan
  [speckit-converge]=converge-shaktimaan
  [speckit-taskstoissues]=taskstoissues-shaktimaan
  [speckit-constitution]=constitution-shaktimaan
)

# Longest old-name first, so e.g. speckit-taskstoissues is replaced before speckit-tasks.
ORDERED_OLD=(speckit-taskstoissues speckit-constitution speckit-checklist speckit-implement speckit-converge speckit-analyze speckit-specify speckit-clarify speckit-plan speckit-tasks)

for old in "${ORDERED_OLD[@]}"; do
  new="${RENAME[$old]}"
  mkdir -p "src/shaktimaan/presets/core/$new"

  sed_args=()
  for o in "${ORDERED_OLD[@]}"; do
    sed_args+=(-e "s/$o/${RENAME[$o]}/g")
  done

  sed \
    "${sed_args[@]}" \
    -e '/^  author: "github-spec-kit"$/d' \
    -e '/^  source: "templates\/commands\//d' \
    -e 's#\.specify/#.shaktimaan/#g' \
    -e "s#Requires spec-kit project structure with \.shaktimaan/ directory#Requires .shaktimaan/ scaffolding (run \`shaktimaan init\` first)#" \
    "$SOURCE_REPO/.claude/skills/$old/SKILL.md" > "src/shaktimaan/presets/core/$new/SKILL.md"
done
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_presets_core_speckit.py -v`
Expected: PASS

If it fails on a leftover `metadata:` line with nothing under it (since only `author`/`source` were deleted), open the affected file(s) and remove the now-empty `metadata:` key by hand — the `sed` above only deletes its two children.

- [ ] **Step 5: Commit**

```bash
git add src/shaktimaan/presets/core/specify-shaktimaan src/shaktimaan/presets/core/clarify-shaktimaan src/shaktimaan/presets/core/plan-shaktimaan src/shaktimaan/presets/core/tasks-shaktimaan src/shaktimaan/presets/core/analyze-shaktimaan src/shaktimaan/presets/core/checklist-shaktimaan src/shaktimaan/presets/core/implement-shaktimaan src/shaktimaan/presets/core/converge-shaktimaan src/shaktimaan/presets/core/taskstoissues-shaktimaan src/shaktimaan/presets/core/constitution-shaktimaan tests/test_presets_core_speckit.py
git commit -m "Port the 10 spec-kit-shaped command skills, renamed to *-shaktimaan"
```

- [ ] **Step 6: Fix lingering `/speckit-*` cross-references in the Task 4 static assets**

Task 4 ported `presets/scripts/bash/*.sh` and `presets/templates/*.md` before these 10 commands
had their final names, so some of them still say things like `/speckit-specify` or
`/speckit-clarify` in user-facing hint text. Now that the mapping is known, fix it:

```bash
FILES=(
  src/shaktimaan/presets/scripts/bash/check-prerequisites.sh
  src/shaktimaan/presets/scripts/bash/setup-tasks.sh
  src/shaktimaan/presets/templates/checklist-template.md
)

sed_args=()
for old in "${ORDERED_OLD[@]}"; do
  sed_args+=(-e "s#/$old#/${RENAME[$old]}#g")
done

for f in "${FILES[@]}"; do
  sed -i "${sed_args[@]}" "$f"
done

grep -rn '/speckit-' src/shaktimaan/presets/scripts src/shaktimaan/presets/templates || echo "clean"
```

(`ORDERED_OLD` and `RENAME` are the same associative array and ordered list from Step 3 above —
reuse them in the same shell session, or redeclare identically if running this step separately.)

Expected: the final `grep` prints `clean` (no remaining `/speckit-` cross-references). If it
finds any, they're in a file this step didn't anticipate — add that file to `FILES` and re-run.

```bash
git add src/shaktimaan/presets/scripts src/shaktimaan/presets/templates
git commit -m "Fix lingering /speckit-* cross-references now that commands have final names"
```

---

### Task 6: Write the 7 config-aware command skills

Unlike Task 5's batch, these seven read `.shaktimaan/config.yml` at runtime instead of taking any project-specific path as given — write their full final content directly (no source-porting script; the content below **is** the deliverable).

**Files:**
- Create: `src/shaktimaan/presets/core/commit-push-shaktimaan/SKILL.md`
- Create: `src/shaktimaan/presets/core/prioritise-next-shaktimaan/SKILL.md`
- Create: `src/shaktimaan/presets/core/new-requirements-shaktimaan/SKILL.md`
- Create: `src/shaktimaan/presets/core/requirements-sync-shaktimaan/SKILL.md`
- Create: `src/shaktimaan/presets/core/feature-tracker-shaktimaan/SKILL.md`
- Create: `src/shaktimaan/presets/core/update-requirements-shaktimaan/SKILL.md`
- Create: `src/shaktimaan/presets/core/readme-shaktimaan/SKILL.md`
- Create: `tests/test_presets_core_original.py`

**Interfaces:**
- Produces: 7 skill directories under `src/shaktimaan/presets/core/`, consumed by Task 8's `install_presets`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_presets_core_original.py
from pathlib import Path

CORE = Path(__file__).parent.parent / "src" / "shaktimaan" / "presets" / "core"

NAMES = [
    "commit-push-shaktimaan",
    "prioritise-next-shaktimaan",
    "new-requirements-shaktimaan",
    "requirements-sync-shaktimaan",
    "feature-tracker-shaktimaan",
    "update-requirements-shaktimaan",
    "readme-shaktimaan",
]


def test_each_skill_exists_reads_config_and_has_no_hardcoded_paths():
    for name in NAMES:
        skill_file = CORE / name / "SKILL.md"
        assert skill_file.exists(), f"missing {skill_file}"
        text = skill_file.read_text()
        assert f'name: "{name}"' in text
        assert ".shaktimaan/config.yml" in text
        assert "requirements/" not in text  # no hardcoded example path left in prose
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_presets_core_original.py -v`
Expected: FAIL — files don't exist yet.

- [ ] **Step 3: Create `src/shaktimaan/presets/core/commit-push-shaktimaan/SKILL.md`**

```markdown
---
name: "commit-push-shaktimaan"
description: "Stage, commit, and push the current changes using this project's configured git identity and commit-message conventions (no Co-Authored-By or Generated-with trailers unless the project asks for one)."
argument-hint: "Optional commit message override"
compatibility: "Requires .shaktimaan/config.yml (run `shaktimaan init` first)"
user-invocable: true
disable-model-invocation: false
model: sonnet
---

## User Input

```text
$ARGUMENTS
```

If non-empty, use this as the commit message (still validate it makes sense against the diff).
Otherwise derive a concise message from the staged/unstaged diff.

## Pre-Execution Checks

**Check for extension hooks (before commit-push)**:
- Check if `.shaktimaan/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_commit_push` key.
- If the YAML cannot be parsed or is invalid, do not skip silently: tell the user that
  `.shaktimaan/extensions.yml` could not be read (include the parser error) and that no hooks
  were checked, including any mandatory (`optional: false`) hooks registered there, then
  continue normally.
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field
  as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition`
  expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable.
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to
    the HookExecutor implementation.
- For each executable hook, output the following based on its `optional` flag:
  - **Optional hook** (`optional: true`):
    ```
    ## Extension Hooks

    **Optional Pre-Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```
  - **Mandatory hook** (`optional: false`):
    ```
    ## Extension Hooks

    **Automatic Pre-Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}

    Wait for the result of the hook command before proceeding to Steps.
    ```
    After emitting the block above you MUST actually invoke the hook and wait for it to finish
    before continuing to Steps below. Emitting the block alone does not run the hook.
- If no hooks are registered or `.shaktimaan/extensions.yml` does not exist, skip silently.

## Steps

1. Read `.shaktimaan/config.yml` for `git_user_name` and `git_user_email`. If the file doesn't
   exist, **STOP** and tell the user to run `shaktimaan init` first.

2. Run `git status` and `git diff` (staged and unstaged) to see what actually changed —
   including any changes a `before_commit_push` hook just made. Flag anything that looks like a
   secret (`.env`, credentials, private keys, tokens) to the user before staging it — never
   commit those silently.

3. **Verify git identity** — run `git config --local user.name` and
   `git config --local user.email`. They MUST resolve to exactly the `git_user_name` /
   `git_user_email` values read in step 1.

   If either is unset or different, **STOP** and tell the user to fix `git config --local
   user.name` / `user.email` first. Never silently fall back to a different identity, and never
   set one yourself without being asked to.

4. Stage the relevant files **by name** — never `git add -A` or `git add .`. Call out any file
   in the diff that looks unintended or unrelated to the change being committed. If a
   `before_commit_push` hook modified a file (e.g. README.md), include it by name so it lands in
   this same commit.

5. Commit with a concise message focused on *why*, passed via a heredoc for correct formatting.
   Do **not** append a `Co-Authored-By:` trailer or any "Generated with Claude Code" line unless
   this project's own conventions explicitly ask for one.

6. Push the current branch to its tracked remote: `git push`, or
   `git push -u origin <branch>` if it has no upstream yet.
   - If the branch is `main`/`master`, or pushing would require `--force`/`--force-with-lease`,
     **STOP** and ask the user first — this command never force-pushes and never pushes over
     history it didn't just create.

7. Report the commit hash, branch name, and remote/branch pushed to.

## Done When

- [ ] Extension hooks (`before_commit_push`) dispatched or skipped according to the rules in
      Pre-Execution Checks above
- [ ] Changes staged by name (no blanket `add -A`) and no secrets committed
- [ ] Git identity verified against `.shaktimaan/config.yml` before committing
- [ ] Commit created with no unwanted attribution trailer
- [ ] Branch pushed to its remote (or the user was asked first, for a force-push case)
- [ ] Commit hash and branch reported to the user
```

- [ ] **Step 4: Create `src/shaktimaan/presets/core/prioritise-next-shaktimaan/SKILL.md`**

```markdown
---
name: "prioritise-next-shaktimaan"
description: "Use when asked which feature to spec next, to prioritize the backlog, or for a ready-to-paste feature description for specify-shaktimaan — reads the project's requirements file, feature tracker, constitution, and any prior research, cross-references specs/ and the requirements-status file, and recommends the smallest slice that is a complete, production-deployable increment."
model: sonnet
---

# Prioritizing the next spec

This is a **read-only recommendation** skill — it doesn't write to any requirements, tracker, or
spec file. It answers "what should `specify-shaktimaan` build next?" by combining six sources of
truth, each owned elsewhere:

| Source | What it gives you |
|---|---|
| `requirements_file` (from `.shaktimaan/config.yml`) | Requirement IDs, Priority (MVP/Phase 2/Later), and the full requirement text |
| `feature_tracker_file` (from `.shaktimaan/config.yml`) | Feature-area status (Not Started/In Progress/Delivered/Blocked) + any "Recommended build order" section |
| `.shaktimaan/memory/constitution.md` | Governing principles that can reorder priority (if `constitution-shaktimaan` has been run) |
| `specs/` | Which slices already have a spec started or complete |
| `specs/*/research.md` | Technical findings/constraints from prior `plan-shaktimaan` runs that may affect what's feasible next |
| `requirements_status_file` (from `.shaktimaan/config.yml`) | Per-ID delivery status + any "Deferred / Gap follow-ups" section |

## Steps

1. Read `.shaktimaan/config.yml` for `requirements_file`, `feature_tracker_file`, and
   `requirements_status_file`. If any is unset, tell the user this project hasn't configured
   requirements tracking and stop — this skill has nothing to prioritize against without it.
2. Read `.shaktimaan/memory/constitution.md` if it exists. Note any principle that bears on
   prioritization order — e.g. a "security first" or "mobile first" principle, or explicit
   sequencing guidance. If the file doesn't exist, skip silently: not every project runs
   `constitution-shaktimaan` before this, and that's fine.
3. Read `feature_tracker_file` in full — its status summary and any "Recommended build order"
   section. This is the primary ranking signal; don't re-derive priority from scratch.
4. Read `requirements_file` in full — Priority tags, the full requirement text, and any
   acceptance-scenario section. The tracker tells you *which* area ranks first; this file is
   what steps 8 and 9 below actually test candidates against.
5. Read `requirements_status_file` if it exists, specifically any "Deferred / Gap follow-ups"
   section — requirement IDs a prior spec touched but didn't fully deliver. A gap that fits
   inside the next candidate feature area should be surfaced as something to fold in.
6. List `specs/` to see what already has a directory — don't recommend a slice that's already
   been speced. A tracker status of "In Progress" only means *some* spec exists for that area,
   not that the whole area is covered — check the spec's own completion state rather than
   skipping the area outright.
7. Read any `specs/*/research.md` files found in step 6. These carry technical findings or
   constraints discovered during a prior feature's planning — e.g. "library X doesn't support Y,"
   or a dependency that turned out to be harder than expected. If one bears on a candidate area
   for this recommendation (makes it easier, harder, or reveals a new dependency), factor it in.
8. Rank remaining candidates:
   - Prefer **Not Started** feature areas over **In Progress** ones.
   - Within Not Started areas, use the tracker's build-order signal first, then MVP-priority
     requirement count as a tiebreaker.
   - If a constitution principle from step 2 clearly favors one candidate over another (e.g. a
     security-first principle and a security-related area is in contention), let it move that
     area up — but say so explicitly in the recommendation rather than silently reordering.
   - An area marked **Blocked** is never the recommendation — surface the blocker instead and
     move to the next candidate.
   - If every Not Started area is blocked, say so explicitly rather than picking one anyway.
9. **Size the slice to the smallest unit that is still a complete, production-deployable
   increment.** Once step 8 picks a candidate feature area, do not default to speccing that
   area's entire requirement set in one spec. Using the requirement text read in step 4, find the
   smallest subset of its requirement IDs that clears all three bars below — this is a size
   *ceiling*, not a target:
   - **Deployable as-is**: shipping to production with only this subset built leaves no broken,
     half-wired, or misleading surface.
   - **Independently verifiable**: the subset maps to at least one acceptance scenario that can
     pass **end-to-end** on its own.
   - **No forward dependency on undelivered work**: nothing in the subset requires a requirement
     ID that lives in a Not Started or Blocked area to actually function (see step 10).
   - If no subset of the top-ranked area clears all three bars, say so and either scope the
     whole area or fall through to the next candidate from step 8.
10. Cross-check dependency shape: read the requirement text for the sized subset's IDs for
    references to other areas. If a dependency is itself Not Started or Blocked, either fold its
    minimum slice into this one or name the dependency order explicitly in the recommendation.
11. Produce a single recommendation (not a ranked list):
    - **Feature area(s)** and the exact requirement IDs in scope.
    - **Why this one now** — cite the build-order/priority signal, any constitution principle
      that influenced the choice, and why this subset is the smallest slice that still clears
      the three deployability bars.
    - **Any relevant prior research** from step 7 that affects how this slice should be scoped.
    - **What's explicitly left out and why**.
    - **Any Deferred / Gap follow-ups to fold in**, if step 5 found ones that plausibly fit.
    - **A ready-to-paste feature description** — 2-4 plain-language WHAT/WHY sentences, no
      implementation detail, so the user can hand it straight to `specify-shaktimaan`.

## What this skill does NOT do

- Does not run `specify-shaktimaan` itself, or create/modify any file under `specs/` or the
  requirements files — recommendation only.
- Does not re-litigate the tracker's status calls — if it looks stale, say so and suggest
  `feature-tracker-shaktimaan` rather than overriding it silently.
- Does not invent requirement IDs or requirement text — every claim traces back to
  `requirements_file`.
- Does not treat the constitution as an override of MVP-priority — it's a tiebreaker/signal
  among Not-Started candidates, not a reason to jump ahead of a Blocked or already-In-Progress
  area's own status.
```

- [ ] **Step 5: Create `src/shaktimaan/presets/core/new-requirements-shaktimaan/SKILL.md`**

```markdown
---
name: "new-requirements-shaktimaan"
description: "Use when bootstrapping a project's requirements from scratch — the first time this project defines its requirements file. Interactively elicits requirements via clarifying questions, writes a versioned structured requirements file, and seeds the feature-tracker file's initial feature-area breakdown."
model: sonnet
---

# Bootstrapping requirements from scratch

This is the **first-time creation** flow — for ongoing edits after `requirements_file` exists,
use `update-requirements-shaktimaan` instead.

## Steps

1. Read `.shaktimaan/config.yml` for `project_name`, `requirements_file`, and
   `feature_tracker_file`. If the config file doesn't exist, **STOP** and tell the user to run
   `shaktimaan init` first.
2. Check whether `requirements_file` already exists. If it does, **STOP** and tell the user to
   use `update-requirements-shaktimaan` for edits instead — this flow only runs once, to create it.
3. Take the user's freeform description of what they want to build — however much or little
   detail they gave.
4. Ask clarifying questions where the input is ambiguous or underspecified: actor/user types,
   MVP vs. later scope, anything with multiple reasonable interpretations. Don't over-ask — only
   ask what materially changes scope or structure. Present them together, then wait for answers.
5. Organize the elicited requirements into capability areas (feature areas) — group related
   behaviors together (e.g. "user identity and access," "core workflow"). Use the same structure
   `update-requirements-shaktimaan` and `feature-tracker-shaktimaan` expect going forward: functional
   and non-functional requirements as separate ID namespaces (`FR-xxx`, `NFR-xxx`), sequential
   within each area's number block, each tagged **MVP** / **Phase 2** / **Later** priority.
6. Write `requirements_file`:
   - A short overview section (what the project is, 2-3 sentences, using `project_name`).
   - Priority definitions (MVP / Phase 2 / Later — the same three tiers `update-requirements-shaktimaan`
     expects).
   - One functional-requirement table per capability area.
   - A non-functional-requirements section, same area-grouped structure.
   - A version header, starting at **v1.0.0** — this is the first version;
     `update-requirements-shaktimaan` owns bumping it from here on.
   - A Changelog section with one entry: "v1.0.0 — initial requirements."
7. Write `feature_tracker_file` — the initial feature-area status snapshot: one row per
   capability area from steps 5/6, all starting at status **Not Started**, plus a Summary table
   and a per-area detail section for each. This is the same file `feature-tracker-shaktimaan`
   maintains going forward; this command only creates its first version.
8. Report both file paths and a short summary of the capability areas created.

## What this skill does NOT do

- Does not run if `requirements_file` already exists — that's `update-requirements-shaktimaan`'s job
  (editing, adding, reconciling, version-bumping).
- Does not create `specs/` directories or run any spec-kit-shaped command — that starts with
  `prioritise-next-shaktimaan` or `specify-shaktimaan` once requirements exist.
- Does not write `.shaktimaan/memory/constitution.md` — that's `constitution-shaktimaan`'s job.
```

- [ ] **Step 6: Create `src/shaktimaan/presets/core/requirements-sync-shaktimaan/SKILL.md`**

```markdown
---
name: "requirements-sync-shaktimaan"
description: "Use when a spec-kit-shaped feature spec (specs/NNN-slug/) is created or updated, or when asked for this project's requirements delivery status, to trace specs back to requirement IDs and keep the requirements-status file current"
model: sonnet
---

# Reconciling specs against the requirements file

This project's requirements (`requirements_file`, from `.shaktimaan/config.yml`) are the
**immutable-per-version requirement source**. The `specs/<NNN>-<slug>/spec.md`, `plan.md`,
`tasks.md` files are the **delivery mechanism** for a given slice of those requirements. This
skill keeps the two connected without letting either drift silently out of sync.

## When a new or updated spec appears

1. Read `.shaktimaan/config.yml` for `requirements_file` and `requirements_status_file`.
2. Read `specs/<NNN>-<slug>/spec.md` (and `plan.md` if present).
3. Search `requirements_file` for every requirement ID that spec's described behavior implements
   or partially implements. Be specific — cite IDs, don't summarize.
4. **If the spec describes behavior with no matching requirement:** stop and flag it to the
   user. Either it's a legitimate new requirement — use `update-requirements-shaktimaan` to propose
   adding it before treating it as in scope — or it's scope creep relative to the requirements
   file — surface that explicitly rather than quietly implementing it. Do not invent a
   requirement mapping just to make the spec look covered.
5. Update `requirements_status_file` (create it on first use — see format below). Add or update
   one row per requirement ID the spec touches.
6. Use `feature-tracker-shaktimaan` to roll this up: find the feature area(s) that own the
   requirement IDs just touched, and move that area's status forward if warranted (e.g. Not
   Started → In Progress the first time a spec targets it). Don't mark an area Delivered from
   this step alone.

## requirements_status_file format

Create lazily — only rows for IDs some spec has actually touched. Table columns:

| ID | Requirement (short) | Status | Spec | Notes |
|---|---|---|---|---|

- **Status** is one of: `Not Started`, `In Progress`, `Done`, `Blocked`.
- **Spec** links to `specs/<NNN>-<slug>/spec.md` (relative path).
- **Notes** captures anything a reviewer needs (partial coverage, deviation from the wording and
  why, follow-up needed).
- One requirement ID may span multiple specs (list them comma-separated) if a large requirement
  is delivered incrementally.

### `## Deferred / Gap follow-ups` section

A separate section, after the main table, owned jointly by `converge-shaktimaan` (which appends
to it) and `specify-shaktimaan` (which reads it and removes an entry once folded into a new
feature's scope). Format: one bullet per gap, `- <ID>: <what remains unaddressed and why>
(surfaced by convergence on specs/<NNN>-<slug>)`. This skill doesn't write to this section
directly, but when reconciling a spec that folded in a previously deferred ID, confirm the
corresponding bullet was removed — if it wasn't, remove it as part of the sync.

## What this skill does NOT do

- It does not edit `requirements_file` — that file's content changes only via
  `update-requirements-shaktimaan`, with explicit user confirmation for new requirements.
- It does not mark something `Done` from the spec alone — only mark `Done` once told the
  implementation is merged/verified.
- It does not update `feature_tracker_file` directly — that's owned by
  `feature-tracker-shaktimaan` (invoke it as step 6 above).

## When asked for "requirements status" or "what's left"

For a quick, feature-area-level answer, read `feature_tracker_file` instead — it's always
present and doesn't require any spec work to exist yet. For per-requirement detail, read
`requirements_status_file` if present, cross-reference against `requirements_file`, and report:
covered-by-some-spec vs. not yet referenced, grouped by Priority. If the status file doesn't
exist yet, say so — it means no spec work has been reconciled yet, not that everything is done.
```

- [ ] **Step 7: Create `src/shaktimaan/presets/core/feature-tracker-shaktimaan/SKILL.md`**

```markdown
---
name: "feature-tracker-shaktimaan"
description: "Use when a feature area's delivery status changes in the feature-tracker file (Not Started / In Progress / Delivered / Blocked) — typically when spec work starts or completes for a feature area, or when asked for the current build/status snapshot of this project's features."
model: sonnet
---

# Updating the feature tracker

`feature_tracker_file` (from `.shaktimaan/config.yml`) is a **live status snapshot** over the
feature areas defined in `requirements_file`. It answers one question the requirements file
deliberately doesn't: *what's actually built right now?*

This is a different artifact from `requirements_status_file` (owned by
`requirements-sync-shaktimaan`) — know which one to touch:

| | Feature tracker | Requirements-status file |
|---|---|---|
| Granularity | Whole feature area | Individual requirement ID |
| Exists | Always (created up front) | Lazily, only once spec work begins |
| Source of truth for | "Is this feature area usable yet, and in what order should we build the rest?" | "Which spec delivers this requirement, and is it done?" |
| Updated by | This skill | `requirements-sync-shaktimaan` |

Update **both** when a spec both touches new requirement IDs and moves a whole feature area's
status — run `requirements-sync-shaktimaan` for the per-ID table, then this skill for the
feature-area rollup. They should never disagree about whether something is done.

## What never changes here

- Don't restate or edit requirement text — that lives only in `requirements_file`.
- Don't invent a new feature area or renumber the existing ones — they should mirror
  `requirements_file`'s own section structure exactly. If that file adds or removes a section,
  reconcile this file's summary and detail sections in the same change.
- The tracker carries no independent version number (unlike `requirements_file`) — it's a living
  snapshot, not a frozen per-version spec. Edit in place; no changelog entry needed.

## When to update a feature area's status

- **Not Started → In Progress**: a `specs/<NNN>-<slug>/` spec is created (or an existing one is
  picked up) whose requirement IDs fall in that feature area's range.
- **In Progress → Delivered (MVP)**: every MVP-priority requirement in that feature area is
  implemented and passing its acceptance scenario(s). Verify, don't infer from "the code looks
  done" — a spec being written, or tasks being marked done, is not by itself delivery.
- **Delivered (MVP) → Delivered (Full)**: the remaining Phase 2 / Later requirements in that
  area are also implemented and passing acceptance.
- **→ Blocked**: work on the area can't proceed. Note the blocker inline in that area's detail
  entry.
- Never mark an area "Delivered" from a spec or a task list alone — only once told (or having
  verified) the implementation is merged and its acceptance scenarios pass.

## How to update

1. Open `feature_tracker_file`.
2. Update the **Status** cell in the summary table row for the affected feature area(s).
3. Update the matching **Status** line in that area's detail section. Keep the two in sync.
4. If status moved because of specific spec work, it's fine to note which spec in the detail
   entry, but don't turn this into a second copy of `requirements_status_file`.
5. Leave any "Recommended build order" section alone unless the user asks to re-sequence it.

## When asked for "what's done" or "what's left"

Read `feature_tracker_file` directly and report by status group, MVP-priority areas first. If
finer per-requirement detail is needed, cross-reference `requirements_status_file` if it exists.
```

- [ ] **Step 8: Create `src/shaktimaan/presets/core/update-requirements-shaktimaan/SKILL.md`**

```markdown
---
name: "update-requirements-shaktimaan"
description: "Use when adding, editing, removing, or reconciling requirements or acceptance scenarios in this project's requirements file, or when bumping its version"
model: sonnet
---

# Updating the requirements file

`requirements_file` (from `.shaktimaan/config.yml`) is the **single consolidated requirements
source** for this project. Do not recreate separate functional/non-functional/roadmap files
unless the project explicitly wants that structure — consolidation into one file is the default
this skill assumes.

## Before editing

1. Read the target section fully — don't pattern-match on one row. Requirement tables are
   typically grouped by capability area, with IDs sequential within that area's number block.
2. Check whether an existing requirement already covers the request. If it's a refinement,
   prefer tightening existing wording over adding a near-duplicate ID.

## ID rules

- Functional and non-functional requirement IDs are separate namespaces; never reuse a number
  across them or across sections.
- New requirement in an existing section → next unused sequential number in that section's
  block.
- **Never renumber or reuse a retired ID.** If a requirement is removed, strike it from the
  table and note the retirement + reason in the Changelog — the ID stays retired, not
  reassigned. Implementation code, tests, and specs may reference these IDs directly.
- Every requirement row needs a **Priority**: MVP / Phase 2 / Later, using whatever definitions
  are already stated near the top of the doc — don't invent new priority labels.

## Don't invent requirements unilaterally

If you're reconciling a spec or an implementation detail that implies behavior not covered by
any existing requirement, **stop and propose it to the user** before adding it — name the
proposed ID, section, wording, and priority, and let them confirm or adjust. Don't skip the
confirmation step just because the gap seems obvious.

## Acceptance-scenario coverage

Any new MVP or Phase 2 requirement that describes observable system behavior should get a
matching acceptance scenario, in Given/When/Then style:

```
**<SCENARIO-ID> — <short title>** `[<requirement IDs it verifies>]`
- Given <precondition>
- When <action>
- Then <observable, testable outcome>
```

Tag it with every requirement ID it verifies. Put it in the existing subsection for that
capability area (add a new one only if no existing area fits). `Later`-priority requirements may
skip this if there's nothing concretely testable yet, but note that explicitly rather than
silently omitting it.

## Versioning and changelog

The doc carries its own version, independent of the project's own release version. On any
change that adds, removes, or materially changes a requirement:

1. Bump the version (minor version for added/changed requirements; patch version only for pure
   wording/typo fixes that change no meaning).
2. Add a **Changelog** entry at the top describing what changed and why — follow the existing
   entry's format.
3. Do not edit past changelog entries to reflect new changes — append a new entry.
```

- [ ] **Step 9: Create `src/shaktimaan/presets/core/readme-shaktimaan/SKILL.md`**

```markdown
---
name: "readme-shaktimaan"
description: "Use when README.md needs to reflect current project state — typically as the before_commit_push extension hook, or when explicitly asked to refresh the README — keeps a standard GitHub front-door README (badges, setup instructions, feature-status table) in sync with the project's manifest and the feature-tracker file."
model: haiku
---

# Keeping README.md current

`README.md` is the **GitHub front door**. Keep it smaller than any fuller project documentation
— condense, don't copy.

## What README.md contains, in order

1. **Title + one-line description** — from the project's manifest file (`package.json`,
   `pyproject.toml`, etc. — whichever this project uses).
2. **Badges row**:
   - **Build** — the real CI status badge for this project's CI workflow, if one exists. Derive
     `<owner>/<repo>` from `git remote get-url origin` — never hardcode it.
   - **Code quality** — a **static** badge naming whatever formatting/lint tooling is actually
     configured. Do **not** fabricate a live quality/coverage score badge for a service that
     isn't actually integrated with this repo.
3. **Overview** — 2-3 sentences condensed from the project's fuller documentation, if one
   exists. Paraphrase for a GitHub skimmer; don't paste that text verbatim.
4. **Setup / run instructions** — derived from the project's actual build/run/test scripts. Keep
   this in sync with whatever scripts actually exist.
5. **Feature status** — if `feature_tracker_file` (from `.shaktimaan/config.yml`) exists, a
   condensed table: just Feature Area and Status columns. Sort Delivered first, then In
   Progress, then Not Started, with any Blocked area called out. Link to the full file rather
   than reproducing it.
6. **Links** — to any fuller project documentation and the requirements file, if they exist.

## Steps

1. Read `.shaktimaan/config.yml` for `project_name` and `feature_tracker_file`.
2. Read the project's manifest file for name/description/scripts.
3. If `feature_tracker_file` is set and exists, read its status summary table.
4. Run `git remote get-url origin` to derive `<owner>/<repo>` for the CI badge URL.
5. If `README.md` doesn't exist, create it with the full structure above. If it exists, update
   only the sections this skill owns — badges, overview, setup instructions, and the
   feature-status table — in place. Leave any other human-written content untouched.
6. Keep it terse. This is a landing page, not documentation.

## What this skill does NOT do

- Does not duplicate fuller project documentation — condenses it, never copies it verbatim.
- Does not fabricate a live code-quality or coverage badge for a service that isn't actually
  integrated with this repo.
- Does not modify `feature_tracker_file` or any other requirements file — read-only there.
```

- [ ] **Step 10: Run test to verify it passes**

Run: `uv run pytest tests/test_presets_core_original.py -v`
Expected: PASS

- [ ] **Step 11: Commit**

```bash
git add src/shaktimaan/presets/core/commit-push-shaktimaan src/shaktimaan/presets/core/prioritise-next-shaktimaan src/shaktimaan/presets/core/new-requirements-shaktimaan src/shaktimaan/presets/core/requirements-sync-shaktimaan src/shaktimaan/presets/core/feature-tracker-shaktimaan src/shaktimaan/presets/core/update-requirements-shaktimaan src/shaktimaan/presets/core/readme-shaktimaan tests/test_presets_core_original.py
git commit -m "Write the 7 config-aware command skills (commit-push, prioritise-next, requirements bundle)"
```

---

### Task 7: Seed `.shaktimaan/extensions.yml`

**Files:**
- Create: `src/shaktimaan/presets/scaffolding/extensions.yml`
- Create: `tests/test_presets_extensions.py`

**Interfaces:**
- Produces: `src/shaktimaan/presets/scaffolding/extensions.yml`, copied verbatim by Task 8's `install_presets` into `<target>/.shaktimaan/extensions.yml`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_presets_extensions.py
from pathlib import Path

import yaml

EXTENSIONS = (
    Path(__file__).parent.parent
    / "src" / "shaktimaan" / "presets" / "scaffolding" / "extensions.yml"
)


def test_extensions_yml_parses_and_has_expected_hooks():
    data = yaml.safe_load(EXTENSIONS.read_text())

    assert set(data["hooks"].keys()) == {
        "after_specify",
        "after_implement",
        "after_converge",
        "after_tasks",
        "before_commit_push",
    }

    for hook_name, entries in data["hooks"].items():
        for entry in entries:
            assert entry["command"].endswith("-shaktimaan"), entry["command"]
            assert "speckit" not in entry["command"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_presets_extensions.py -v`
Expected: FAIL — file doesn't exist yet.

- [ ] **Step 3: Create `src/shaktimaan/presets/scaffolding/extensions.yml`**

```yaml
# Extension hooks for shaktimaan commands.
#
# These wire the requirements-tracking bundle into the spec lifecycle so
# requirements_status_file and feature_tracker_file (see .shaktimaan/config.yml)
# stay current without needing to be run by hand after every
# specify-shaktimaan, implement-shaktimaan, or converge-shaktimaan.

hooks:
  after_specify:
    - extension: requirements-tracking
      command: requirements-sync-shaktimaan
      optional: false
      description: >-
        Trace the new/updated spec's requirement IDs against the
        requirements file and update the requirements-status file.
      prompt: >-
        A spec was just created or updated. Use the requirements-sync-shaktimaan
        skill to trace this spec's requirement IDs against requirements_file
        and update requirements_status_file. If the spec implies behavior
        with no matching requirement, stop and flag it rather than
        inventing a mapping.
    - extension: requirements-tracking
      command: feature-tracker-shaktimaan
      optional: false
      description: >-
        Roll the feature area(s) covering this spec's requirement IDs
        forward in the feature tracker.
      prompt: >-
        Use the feature-tracker-shaktimaan skill to roll the feature
        area(s) that own the requirement IDs just traced forward in
        feature_tracker_file — typically Not Started to In Progress the
        first time a spec targets that area. Do not mark any area
        Delivered at this stage.

  after_implement:
    - extension: requirements-tracking
      command: requirements-sync-shaktimaan
      optional: false
      description: >-
        Re-check which requirement IDs this spec's completed tasks
        actually deliver, and update the requirements-status file.
      prompt: >-
        Implementation tasks for this feature's spec were just executed.
        Use the requirements-sync-shaktimaan skill to re-check
        requirements_status_file against which requirement IDs this spec
        delivers. Mark an ID Done only if you can verify it's implemented
        and passing its acceptance scenario(s) — tasks.md showing complete
        is not by itself verification.
    - extension: requirements-tracking
      command: feature-tracker-shaktimaan
      optional: false
      description: >-
        Roll the feature tracker forward for any feature area now fully
        delivered.
      prompt: >-
        Use the feature-tracker-shaktimaan skill to roll feature_tracker_file
        forward for any feature area now fully delivered at MVP or Full
        level. Leave areas only partially covered by this spec as In
        Progress.

  after_converge:
    - extension: requirements-tracking
      command: requirements-sync-shaktimaan
      optional: false
      description: >-
        Reconcile the requirements-status file against the convergence
        outcome.
      prompt: >-
        converge-shaktimaan just assessed this feature's implementation
        against its spec, plan, and tasks. If the outcome was "converged"
        (no remaining gaps), use requirements-sync-shaktimaan to confirm
        requirements_status_file marks this spec's requirement IDs Done.
        If tasks were instead appended to tasks.md, leave status as In
        Progress.
    - extension: requirements-tracking
      command: feature-tracker-shaktimaan
      optional: false
      description: >-
        Roll the feature tracker forward for any feature area convergence
        confirms is fully delivered.
      prompt: >-
        Use feature-tracker-shaktimaan to roll feature_tracker_file
        forward for any feature area this convergence run confirms is now
        fully delivered.

  after_tasks:
    - extension: requirements-tracking
      command: feature-tracker-shaktimaan
      optional: true
      description: >-
        Optional early status check — tasks.md was (re)generated but not
        yet executed, so this is a preview, not a delivery signal.
      prompt: >-
        tasks.md was just (re)generated for this feature. This is
        optional: if you want a status preview now rather than waiting for
        implement-shaktimaan or converge-shaktimaan, run
        requirements-sync-shaktimaan followed by feature-tracker-shaktimaan.
        Do not mark anything Done or Delivered from tasks.md alone.

  before_commit_push:
    - extension: readme-sync
      command: readme-shaktimaan
      optional: false
      description: >-
        Refresh README.md's badges, setup instructions, and feature-status
        table before this commit is created.
      prompt: >-
        About to stage and commit changes via commit-push-shaktimaan. Use
        the readme-shaktimaan skill to refresh README.md before anything
        is staged.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_presets_extensions.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/shaktimaan/presets/scaffolding/extensions.yml tests/test_presets_extensions.py
git commit -m "Seed default .shaktimaan/extensions.yml with the requirements-tracking hooks"
```

---

### Task 8: Installer — copy presets + write config into a target project

**Files:**
- Create: `src/shaktimaan/installer.py`
- Create: `tests/test_installer.py`

**Interfaces:**
- Consumes: `ShaktimaanConfig` (Task 2); `src/shaktimaan/presets/core/*`, `src/shaktimaan/presets/scripts/*`, `src/shaktimaan/presets/templates/*`, `src/shaktimaan/presets/scaffolding/extensions.yml` (Tasks 4-7).
- Produces: `shaktimaan.installer.install_presets(target_dir: Path, config: ShaktimaanConfig) -> None`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_installer.py
from pathlib import Path

from shaktimaan.config import ShaktimaanConfig
from shaktimaan.installer import install_presets

SAMPLE_CONFIG = ShaktimaanConfig(
    project_name="Example",
    requirements_file="requirements/requirements.md",
    feature_tracker_file="requirements/feature-tracker.md",
    requirements_status_file="docs/REQUIREMENTS-STATUS.md",
    git_user_name="Ada Lovelace",
    git_user_email="ada@example.com",
)


def test_install_presets_copies_all_17_skills(tmp_path):
    install_presets(tmp_path, SAMPLE_CONFIG)

    skills_dir = tmp_path / ".claude" / "skills"
    installed = sorted(p.name for p in skills_dir.iterdir())

    assert len(installed) == 17
    assert "specify-shaktimaan" in installed
    assert "commit-push-shaktimaan" in installed
    assert (skills_dir / "specify-shaktimaan" / "SKILL.md").exists()


def test_install_presets_writes_config_and_extensions(tmp_path):
    install_presets(tmp_path, SAMPLE_CONFIG)

    assert (tmp_path / ".shaktimaan" / "config.yml").exists()
    assert (tmp_path / ".shaktimaan" / "extensions.yml").exists()
    assert (tmp_path / ".shaktimaan" / "scripts" / "bash" / "common.sh").exists()
    assert (tmp_path / ".shaktimaan" / "templates" / "spec-template.md").exists()


def test_install_presets_is_idempotent(tmp_path):
    install_presets(tmp_path, SAMPLE_CONFIG)
    install_presets(tmp_path, SAMPLE_CONFIG)  # must not raise

    skills_dir = tmp_path / ".claude" / "skills"
    assert len(list(skills_dir.iterdir())) == 17
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_installer.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'shaktimaan.installer'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/shaktimaan/installer.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_installer.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/shaktimaan/installer.py tests/test_installer.py
git commit -m "Add install_presets: copies the 17 skills + .shaktimaan scaffolding into a target project"
```

---

### Task 9: Wire `shaktimaan init` end-to-end

**Files:**
- Modify: `src/shaktimaan/cli.py`
- Modify: `tests/test_cli.py`

**Interfaces:**
- Consumes: `collect_config` (Task 3), `install_presets` (Task 8).
- Produces: `shaktimaan init [DIR]` Typer command, with `--yes`/per-field flags for non-interactive use.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_cli.py
from pathlib import Path


def test_init_non_interactive_installs_into_target_dir(tmp_path):
    target = tmp_path / "my-project"
    target.mkdir()

    result = runner.invoke(
        app,
        [
            "init",
            str(target),
            "--project-name", "Example",
            "--requirements-file", "requirements/requirements.md",
            "--feature-tracker-file", "requirements/feature-tracker.md",
            "--requirements-status-file", "docs/REQUIREMENTS-STATUS.md",
            "--git-user-name", "Ada Lovelace",
            "--git-user-email", "ada@example.com",
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert (target / ".claude" / "skills" / "specify-shaktimaan" / "SKILL.md").exists()
    assert (target / ".shaktimaan" / "config.yml").exists()


def test_init_defaults_to_current_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        [
            "init",
            "--project-name", "Example",
            "--requirements-file", "requirements/requirements.md",
            "--feature-tracker-file", "requirements/feature-tracker.md",
            "--requirements-status-file", "docs/REQUIREMENTS-STATUS.md",
            "--git-user-name", "Ada Lovelace",
            "--git-user-email", "ada@example.com",
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert (tmp_path / ".shaktimaan" / "config.yml").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cli.py -v`
Expected: FAIL — no `init` command registered yet.

- [ ] **Step 3: Write minimal implementation**

Append to `src/shaktimaan/cli.py`:

```python
from pathlib import Path
from typing import Optional

from shaktimaan.config import collect_config
from shaktimaan.installer import install_presets


@app.command()
def init(
    directory: Path = typer.Argument(
        Path("."), help="Target project directory (defaults to the current directory)."
    ),
    project_name: Optional[str] = typer.Option(None, "--project-name"),
    requirements_file: Optional[str] = typer.Option(None, "--requirements-file"),
    feature_tracker_file: Optional[str] = typer.Option(None, "--feature-tracker-file"),
    requirements_status_file: Optional[str] = typer.Option(None, "--requirements-status-file"),
    git_user_name: Optional[str] = typer.Option(None, "--git-user-name"),
    git_user_email: Optional[str] = typer.Option(None, "--git-user-email"),
) -> None:
    """Scaffold the shaktimaan command set and .shaktimaan/ config into DIRECTORY."""
    overrides = {
        "project_name": project_name or "",
        "requirements_file": requirements_file or "",
        "feature_tracker_file": feature_tracker_file or "",
        "requirements_status_file": requirements_status_file or "",
        "git_user_name": git_user_name or "",
        "git_user_email": git_user_email or "",
    }

    def prompt_fn(field_name: str, default: str) -> str:
        from shaktimaan.config import FIELD_PROMPTS

        return typer.prompt(FIELD_PROMPTS[field_name], default=default)

    config = collect_config(overrides=overrides, prompt_fn=prompt_fn)

    directory.mkdir(parents=True, exist_ok=True)
    install_presets(directory, config)

    typer.echo(f"Installed 17 shaktimaan commands into {directory / '.claude' / 'skills'}")
    typer.echo(f"Config written to {directory / '.shaktimaan' / 'config.yml'}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_cli.py -v`
Expected: PASS (3 tests total in this file)

- [ ] **Step 5: Commit**

```bash
git add src/shaktimaan/cli.py tests/test_cli.py
git commit -m "Wire shaktimaan init end-to-end with non-interactive flags"
```

---

### Task 10: Package data + full-suite verification

**Files:**
- Modify: `pyproject.toml`

**Interfaces:** none (packaging-only task).

- [ ] **Step 1: Add preset files as package data**

Add to `pyproject.toml`, inside `[tool.hatch.build.targets.wheel]`:

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/shaktimaan"]

[tool.hatch.build.targets.wheel.force-include]
"src/shaktimaan/presets" = "shaktimaan/presets"
```

(Hatchling includes non-`.py` files under `src/shaktimaan/` by default for an editable/sdist
install, but `force-include` guards against silent exclusion in the built wheel — verify in the
next step rather than trusting the default.)

- [ ] **Step 2: Run the full test suite**

Run: `uv run pytest -v`
Expected: PASS — all tests across `test_cli.py`, `test_config.py`, `test_presets_static.py`,
`test_presets_core_speckit.py`, `test_presets_core_original.py`, `test_presets_extensions.py`,
`test_installer.py`.

- [ ] **Step 3: Verify the packaged wheel actually contains the presets**

```bash
uv build
python -c "
import zipfile
whl = sorted(Path('dist').glob('*.whl'))[-1]
names = zipfile.ZipFile(whl).namelist()
assert any('presets/core/specify-shaktimaan/SKILL.md' in n for n in names), names
print('OK: presets present in wheel')
" 2>&1 || uv run python -c "
import zipfile, pathlib
whl = sorted(pathlib.Path('dist').glob('*.whl'))[-1]
names = zipfile.ZipFile(whl).namelist()
assert any('presets/core/specify-shaktimaan/SKILL.md' in n for n in names), names
print('OK: presets present in wheel')
"
```

Expected: prints `OK: presets present in wheel`. If it instead raises `AssertionError`, the
`force-include` mapping in Step 1 is wrong — fix the path and rebuild.

- [ ] **Step 4: Verify local end-to-end install**

```bash
uv tool install --editable . --force
mkdir -p /tmp/shaktimaan-smoke-test
cd /tmp/shaktimaan-smoke-test
shaktimaan init . \
  --project-name "Smoke Test" \
  --requirements-file requirements/requirements.md \
  --feature-tracker-file requirements/feature-tracker.md \
  --requirements-status-file docs/REQUIREMENTS-STATUS.md \
  --git-user-name "Test User" \
  --git-user-email test@example.com
ls .claude/skills | wc -l   # expect 17
cat .shaktimaan/config.yml
cd -
rm -rf /tmp/shaktimaan-smoke-test
```

Expected: `ls .claude/skills | wc -l` prints `17`, and `config.yml` shows the six fields with the
values just passed.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml
git commit -m "Ensure presets are packaged in the built wheel; verify end-to-end install"
```

---

### Task 11: README polish

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Rewrite `README.md`**

```markdown
# Shaktimaan

A personal Spec-Driven Development (SDD) toolkit for Claude Code: a CLI
that scaffolds a `specify → clarify → plan → tasks → analyze → checklist →
implement → converge` workflow into any project, plus `commit-push` and
`prioritise-next`, and a requirements-tracking bundle for PRD-style
projects.

Inspired by [github/spec-kit](https://github.com/github/spec-kit) (MIT
licensed) — same workflow shape, own implementation, own commands.

## Install

```bash
uv tool install shaktimaan-cli
```

## Usage

```bash
shaktimaan init /path/to/your/project
```

Prompts for (or takes as flags):

| Flag | What it's for |
|---|---|
| `--project-name` | Used in generated docs |
| `--requirements-file` | Path to your PRD |
| `--feature-tracker-file` | Path to your feature-status tracker |
| `--requirements-status-file` | Path to your per-requirement delivery-status file |
| `--git-user-name` / `--git-user-email` | The identity `commit-push-shaktimaan` verifies before committing |

Installs 17 Claude Code skills into `.claude/skills/` and scaffolding into
`.shaktimaan/`.

## Commands installed

`specify-shaktimaan`, `clarify-shaktimaan`, `plan-shaktimaan`,
`tasks-shaktimaan`, `analyze-shaktimaan`, `checklist-shaktimaan`,
`implement-shaktimaan`, `converge-shaktimaan`, `taskstoissues-shaktimaan`,
`constitution-shaktimaan`, `commit-push-shaktimaan`,
`prioritise-next-shaktimaan`, `new-requirements-shaktimaan`,
`requirements-sync-shaktimaan`, `feature-tracker-shaktimaan`,
`update-requirements-shaktimaan`, `readme-shaktimaan`.

## Status

v1: Claude Code only. See `docs/superpowers/specs/` for the design doc.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "Write usage README: install, init flags, command list"
```

---

## Self-review notes (already applied above)

- **Spec coverage:** every design-doc section has a task — command set (Tasks 5-6), configurability (Tasks 2-3, and the runtime-lookup correction noted in Global Constraints), target-project layout (Task 8), packaging (Tasks 1, 10), repo layout (Tasks 1-9), provenance/licensing (already committed pre-plan), open question resolution (Task 7 ships the bundle unconditionally, matching "always included").
- **Design correction carried into this plan:** the design doc's `render.py`/`{{PLACEHOLDER}}` wording is superseded by the runtime-config-lookup approach (see Global Constraints) — simpler, and actually matches the design doc's own stated rationale better than literal templating would have.
- **No placeholders:** every task's content is either a real script/config/code block or, for the 7 config-aware skills, the full final file content.
- **Type/name consistency checked:** `ShaktimaanConfig` field names (`project_name`, `requirements_file`, `feature_tracker_file`, `requirements_status_file`, `git_user_name`, `git_user_email`) are identical across Tasks 2, 3, 6 (skill prose), 8, 9, and the CLI flags in Task 9.
