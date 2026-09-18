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


def test_no_leftover_speckit_references_in_scripts():
    for name in SCRIPTS:
        text = (PRESETS / "scripts" / "bash" / name).read_text()
        assert "speckit" not in text.lower(), (
            f"{name} still contains a 'speckit' reference (case-insensitive) "
            "left over from the upstream port"
        )
