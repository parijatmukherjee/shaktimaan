from pathlib import Path

import yaml
from typer.testing import CliRunner

from shaktimaan.cli import app

runner = CliRunner()


def test_version_flag_prints_version_and_exits_zero():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "shaktimaan" in result.stdout.lower()


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


def test_init_prompts_for_omitted_flags(tmp_path, monkeypatch):
    from shaktimaan.config import FIELD_PROMPTS

    target = tmp_path / "my-project"
    target.mkdir()

    prompted_texts = []

    def fake_prompt(text, default=None):
        prompted_texts.append(text)
        return "PROMPTED-VALUE"

    monkeypatch.setattr("shaktimaan.cli.typer.prompt", fake_prompt)

    result = runner.invoke(
        app,
        [
            "init",
            str(target),
            "--project-name", "Example",
        ],
    )

    assert result.exit_code == 0, result.stdout

    omitted_fields = [
        "requirements_file",
        "feature_tracker_file",
        "requirements_status_file",
        "git_user_name",
        "git_user_email",
    ]
    expected_prompt_texts = {FIELD_PROMPTS[field] for field in omitted_fields}
    assert set(prompted_texts) == expected_prompt_texts
    assert len(prompted_texts) == len(omitted_fields)

    config_data = yaml.safe_load((target / ".shaktimaan" / "config.yml").read_text())
    assert config_data["project_name"] == "Example"
    for field in omitted_fields:
        assert config_data[field] == "PROMPTED-VALUE"
