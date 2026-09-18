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


def test_install_presets_does_not_clobber_user_edited_extensions_yml(tmp_path):
    install_presets(tmp_path, SAMPLE_CONFIG)

    extensions_path = tmp_path / ".shaktimaan" / "extensions.yml"
    customization = "# user customization: do not overwrite me\n"
    original = extensions_path.read_text()
    extensions_path.write_text(customization + original)

    install_presets(tmp_path, SAMPLE_CONFIG)  # re-run, e.g. via `shaktimaan init` again

    assert extensions_path.read_text() == customization + original
