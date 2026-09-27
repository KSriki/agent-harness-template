"""init.py --install-hooks: per-hook idempotency, the upgrade path, and doc drift."""

import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("harness_init", REPO / "init.py")
init = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = init  # dataclasses resolve types via sys.modules
spec.loader.exec_module(init)


def events(settings):
    return {
        ev: len(entries)
        for ev, entries in json.loads(settings.read_text())["hooks"].items()
    }


def test_fresh_install_adds_all_three(tmp_path):
    assert init.install_hooks(str(tmp_path)) == 0
    assert events(tmp_path / "settings.json") == {
        "PreToolUse": 1,
        "PostToolUse": 1,
        "Stop": 1,
    }


def test_rerun_is_a_no_op(tmp_path):
    init.install_hooks(str(tmp_path))
    before = (tmp_path / "settings.json").read_text()
    assert init.install_hooks(str(tmp_path)) == 0
    assert (tmp_path / "settings.json").read_text() == before


def test_existing_machine_gains_only_the_guard(tmp_path):
    """A machine installed before the guard existed has gate-dispatch hooks already —
    the old all-or-nothing check would have skipped the guard forever."""
    legacy = json.loads((REPO / "gates/settings-hooks.json").read_text())
    legacy["hooks"].pop("PreToolUse")
    legacy["hooks"]["SessionStart"] = [
        {"hooks": [{"type": "command", "command": "bd prime"}]}
    ]
    (tmp_path / "settings.json").write_text(json.dumps({"hooks": legacy["hooks"]}))
    assert init.install_hooks(str(tmp_path)) == 0
    assert events(tmp_path / "settings.json") == {
        "PostToolUse": 1,
        "Stop": 1,
        "SessionStart": 1,
        "PreToolUse": 1,
    }
    assert (tmp_path / "settings.json.bak").exists()


def test_dry_run_writes_nothing(tmp_path):
    assert init.install_hooks(str(tmp_path), dry_run=True) == 0
    assert not (tmp_path / "settings.json").exists()


def test_invalid_settings_json_is_left_alone(tmp_path):
    (tmp_path / "settings.json").write_text("{broken")
    assert init.install_hooks(str(tmp_path)) == 1
    assert (tmp_path / "settings.json").read_text() == "{broken"


def test_documented_snippet_matches_what_init_installs(tmp_path):
    init.install_hooks(str(tmp_path))
    installed = json.loads((tmp_path / "settings.json").read_text())["hooks"]
    documented = json.loads((REPO / "gates/settings-hooks.json").read_text())["hooks"]
    assert installed == documented
