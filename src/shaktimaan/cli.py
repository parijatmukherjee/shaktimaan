from pathlib import Path
from typing import Optional

import typer

from shaktimaan import __version__
from shaktimaan.config import CONFIG_FIELDS, ConfigError, FIELD_DEFAULTS, collect_config, load_config
from shaktimaan.installer import install_presets

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
    raw = {
        "project_name": project_name,
        "requirements_file": requirements_file,
        "feature_tracker_file": feature_tracker_file,
        "requirements_status_file": requirements_status_file,
        "git_user_name": git_user_name,
        "git_user_email": git_user_email,
    }
    overrides = {k: v for k, v in raw.items() if v is not None}

    existing_config_path = directory / ".shaktimaan" / "config.yml"
    if existing_config_path.exists():
        try:
            existing_config = load_config(existing_config_path)
            defaults = {field: getattr(existing_config, field) for field in CONFIG_FIELDS}
        except ConfigError:
            # Existing config is missing/malformed; fall back to the blank defaults
            # rather than failing `init`, which is also how a first-time install prompts.
            defaults = dict(FIELD_DEFAULTS)
    else:
        defaults = dict(FIELD_DEFAULTS)

    def prompt_fn(field_name: str, default: str) -> str:
        from shaktimaan.config import FIELD_PROMPTS

        return typer.prompt(FIELD_PROMPTS[field_name], default=default)

    config = collect_config(overrides=overrides, prompt_fn=prompt_fn, defaults=defaults)

    directory.mkdir(parents=True, exist_ok=True)
    install_presets(directory, config)

    skills_dir = directory / ".claude" / "skills"
    installed_count = sum(1 for entry in skills_dir.iterdir() if entry.is_dir())

    typer.echo(f"Installed {installed_count} shaktimaan commands into {skills_dir}")
    typer.echo(f"Config written to {directory / '.shaktimaan' / 'config.yml'}")


def main() -> None:
    app()
