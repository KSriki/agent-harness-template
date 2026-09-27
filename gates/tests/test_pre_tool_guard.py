"""pre_tool_guard: the decisions, and the hook contract (stdin JSON → stdout JSON)."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

GATES = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GATES))
import pre_tool_guard as g  # noqa: E402


def bash(cmd, cwd="/repo/proj"):
    v = g.decide({"tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": cwd})
    return v and v["hookSpecificOutput"]["permissionDecision"]


@pytest.mark.parametrize(
    "cmd",
    [
        "git commit --no-verify -m wip",
        "git commit -n -m wip",
        "git commit -anm wip",
        "git push --no-verify",
        "git -c core.hooksPath=/dev/null commit -m x",
        "git config core.hooksPath .nohooks",
        "git push --force origin main",
        "git push -f origin HEAD:master",
        "git push origin +main",
        "cd sub && git push --force-with-lease origin main",
        "bash -c 'git commit --no-verify -m x'",
        "eval git push -f origin main",
        "sudo rm -rf /",
        "rm -rf ~",
        "rm -rf $HOME/stuff",
        "rm -fr *",
        "rm -r -f .",
        "rm -rf ..",
    ],
)
def test_denied(cmd):
    assert bash(cmd) == "deny", cmd


@pytest.mark.parametrize(
    "cmd",
    [
        "git push --force origin feature/x",
        "git push origin --delete feature/x",
        "git reset --hard HEAD~1",
        "git clean -fdx",
        "rm -rf /tmp/elsewhere",
        "npm install left-pad",
        "pnpm add zod",
        "yarn add react",
        "pip install requests",
        "python3 -m pip install requests",
        "uv add httpx",
        "uv pip install httpx",
        "poetry add rich",
        "go get github.com/x/y@v1",
        "cargo add serde",
        "brew install jq",
        "npx some-tool",
        "pnpm dlx create-thing",
        "FOO=1 npm i lodash",
    ],
)
def test_asks(cmd):
    assert bash(cmd) == "ask", cmd


@pytest.mark.parametrize(
    "cmd",
    [
        "git commit -m 'fix: handle --no-verify in docs'",  # inside a quoted message
        "git push origin feature/x",
        "git status && git diff",
        "grep -rn -- --no-verify .",
        "rm -rf build node_modules",
        "rm -f file.txt",
        "npm install",  # lockfile restore, not a new dep
        "npm ci",
        "pip install -r requirements.txt",
        "pip install -e .",
        "uv sync",
        "go build ./...",
        "echo 'rm -rf /'",
        "ls -la",
        "",
    ],
)
def test_allowed(cmd):
    assert bash(cmd) is None, cmd


def test_unbalanced_quotes_fall_back_without_crashing():
    assert bash("git commit --no-verify -m 'oops") == "deny"


def edit(tmp_path, rel, tool="Edit", create=True):
    path = tmp_path / rel
    if create:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x")
    v = g.decide(
        {
            "tool_name": tool,
            "tool_input": {"file_path": str(path)},
            "cwd": str(tmp_path),
        }
    )
    return v and v["hookSpecificOutput"]["permissionDecision"]


@pytest.mark.parametrize(
    "rel",
    [
        ".claude/gate.sh",
        ".github/workflows/gate.yml",
        "ruff.toml",
        "pyproject.toml",
        "package.json",
        "requirements-dev.txt",
        "tsconfig.json",
        "tsconfig.build.json",
        "eslint.config.mjs",
        ".eslintrc.json",
        ".golangci.yml",
        "setup.cfg",
        ".coveragerc",
        "web/vitest.config.ts",
    ],
)
def test_existing_config_edit_asks(tmp_path, rel):
    assert edit(tmp_path, rel) == "ask"
    assert edit(tmp_path, rel, tool="Write") == "ask"


def test_new_config_file_is_scaffolding_not_loosening(tmp_path):
    assert edit(tmp_path, "ruff.toml", tool="Write", create=False) is None


@pytest.mark.parametrize(
    "rel", ["src/app.py", "README.md", "docs/gate.md", "tests/test_x.py"]
)
def test_ordinary_files_allowed(tmp_path, rel):
    assert edit(tmp_path, rel) is None


def test_other_tools_ignored():
    assert (
        g.decide({"tool_name": "Read", "tool_input": {"file_path": "pyproject.toml"}})
        is None
    )


def run_hook(payload, env_extra=None):
    import os

    env = {**os.environ, **(env_extra or {})}
    return subprocess.run(
        [sys.executable, str(GATES / "pre_tool_guard.py")],
        input=payload,
        capture_output=True,
        text=True,
        env=env,
    )


def test_hook_contract_emits_permission_decision_json():
    out = run_hook(
        json.dumps(
            {"tool_name": "Bash", "tool_input": {"command": "git push -f origin main"}}
        )
    )
    assert out.returncode == 0
    decision = json.loads(out.stdout)["hookSpecificOutput"]
    assert decision["hookEventName"] == "PreToolUse"
    assert decision["permissionDecision"] == "deny"
    assert decision["permissionDecisionReason"].startswith("[harness guard]")


def test_hook_allows_silently():
    out = run_hook(json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls"}}))
    assert (out.returncode, out.stdout) == (0, "")


def test_hook_fails_open_on_garbage_input():
    out = run_hook("not json")
    assert out.returncode == 0 and out.stdout == ""
    assert "internal error" in out.stderr


def test_kill_switch():
    payload = json.dumps(
        {"tool_name": "Bash", "tool_input": {"command": "git push -f origin main"}}
    )
    out = run_hook(payload, {"HARNESS_GUARD": "off"})
    assert out.stdout == ""
