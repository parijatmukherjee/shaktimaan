import pytest

from shaktimaan.config import (
    FIELD_DEFAULTS,
    ConfigError,
    ShaktimaanConfig,
    collect_config,
    load_config,
    save_config,
)

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
        assert default == FIELD_DEFAULTS[field_name]
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
