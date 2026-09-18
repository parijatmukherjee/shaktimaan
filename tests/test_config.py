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
