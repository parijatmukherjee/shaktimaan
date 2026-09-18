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
