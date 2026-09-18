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
