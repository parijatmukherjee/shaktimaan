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
