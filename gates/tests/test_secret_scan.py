"""secret_scan: patterns, pragma, and the changed-vs-all file selection in a real git repo.

Fake secrets are assembled at runtime so this file never trips the scanner itself.
"""

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import secret_scan as s  # noqa: E402

FAKES = {
    "AWS access key": "AKIA" + "ABCDEFGHIJKLMNOP",
    "GitHub token": "ghp_" + "a" * 36,
    "Anthropic key": "sk-ant-" + "api03-" + "x" * 30,
    "Slack token": "xoxb-" + "1234567890-abc",
    "Google API key": "AIza" + "B" * 35,
    "Stripe live key": "sk_live_" + "c" * 24,
    "private key": "-----BEGIN " + "RSA PRIVATE KEY-----",
    "credential in URL": "postgres://admin:" + "hunter22" + "@db.internal:5432/x",
}


@pytest.mark.parametrize("name,secret", FAKES.items())
def test_detects(name, secret):
    assert s.scan_text(f'KEY = "{secret}"') == [(1, name)]


@pytest.mark.parametrize(
    "text",
    [
        "API_KEY = os.environ['API_KEY']",
        "url = 'https://example.com/path'",
        "postgres://localhost:5432/db",
        "sk-not-a-real-key",
        "AKIA_short",
    ],
)
def test_ignores_non_secrets(text):
    assert s.scan_text(text) == []


def test_pragma_allows_a_single_line():
    text = f'FIXTURE = "{FAKES["GitHub token"]}"  # {s.PRAGMA}\nREAL = "{FAKES["GitHub token"]}"'
    assert s.scan_text(text) == [(2, "GitHub token")]


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "t@t")
    git(tmp_path, "config", "user.name", "t")
    (tmp_path / "old.py").write_text(f'K = "{FAKES["AWS access key"]}"\n')
    (tmp_path / "clean.py").write_text("x = 1\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "init")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_changed_mode_scans_only_modified_and_untracked(repo, capsys):
    assert s.main([]) == 0  # committed secret is not "changed"
    (repo / "new.py").write_text(f'T = "{FAKES["Slack token"]}"\n')
    assert s.main([]) == 1
    err = capsys.readouterr().err
    assert "new.py:1: possible Slack token" in err and "old.py" not in err


def test_all_mode_scans_tracked_files(repo, capsys):
    assert s.main(["--all"]) == 1
    assert "old.py:1: possible AWS access key" in capsys.readouterr().err


def test_skips_binary_and_huge_files(repo):
    (repo / "blob.bin").write_bytes(b"\0" + FAKES["GitHub token"].encode())
    (repo / "huge.txt").write_text(FAKES["GitHub token"] + "x" * (s.MAX_BYTES + 1))
    assert s.scan_file(repo / "blob.bin") == []
    assert s.scan_file(repo / "huge.txt") == []
    assert s.scan_file(repo / "missing.txt") == []
