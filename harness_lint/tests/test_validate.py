"""harness_lint: each check against a minimal synthetic harness, plus the real repo."""

from pathlib import Path

import pytest

from harness_lint import validate as v

REPO = Path(__file__).resolve().parents[2]

SKILL = """---
name: {name}
description: >
  Use when X. Covers Y.
  Do NOT use for Z.
---
# body
"""

AGENT = """---
name: {name}
description: Use to do a thing.
tools: Read, Grep   # read-only
model: {model}   # comment
skills:
  - {skill}   # preload
---
body
"""


@pytest.fixture
def harness(tmp_path):
    (tmp_path / "skills/tdd").mkdir(parents=True)
    (tmp_path / "skills/tdd/SKILL.md").write_text(SKILL.format(name="tdd"))
    (tmp_path / "agents/eng").mkdir(parents=True)
    (tmp_path / "agents/eng/worker.md").write_text(
        AGENT.format(name="worker", model="sonnet", skill="tdd")
    )
    (tmp_path / "AGENTS.md").write_text(
        "# x\n## Skills available\n| Skill | Use |\n|---|---|\n| `tdd` | t |\n## Next\n"
    )
    return tmp_path


def test_parse_frontmatter_subset():
    fm = v.parse_frontmatter(AGENT.format(name="w", model="opus", skill="tdd"))
    assert fm == {
        "name": "w",
        "description": "Use to do a thing.",
        "tools": "Read, Grep",
        "model": "opus",
        "skills": ["tdd"],
    }
    folded = v.parse_frontmatter(SKILL.format(name="s"))
    assert folded["description"] == "Use when X. Covers Y. Do NOT use for Z."
    assert v.parse_frontmatter('---\nname: "quoted # not comment"\n---') == {
        "name": "quoted # not comment"
    }
    assert v.parse_frontmatter("no frontmatter") is None
    assert v.parse_frontmatter("---\nname: x\n") is None


def test_clean_harness_has_no_findings(harness):
    assert v.check_skills(harness) == []
    assert v.check_agents(harness, {"sonnet", "opus"}) == []
    assert v.check_model_registry(harness, {"worker": "sonnet"}) == []
    assert v.check_skills_index(harness) == []
    assert v.check_links(harness) == []


def test_skill_findings(harness):
    (harness / "skills/bad").mkdir()
    (harness / "skills/bad/SKILL.md").write_text(
        "---\nname: Wrong_Name\ndescription: Use it.\n---\n"
    )
    (harness / "skills/nofm").mkdir()
    (harness / "skills/nofm/SKILL.md").write_text("# no frontmatter\n")
    (harness / "skills/user-only").mkdir()
    (harness / "skills/user-only/SKILL.md").write_text(
        "---\nname: user-only\ndescription: Re-pitch.\ndisable-model-invocation: true\n---\n"
    )
    found = "\n".join(v.check_skills(harness))
    assert "!= directory 'bad'" in found
    assert "not kebab-case" in found
    assert "no NOT-clause" in found
    assert "skills/nofm/SKILL.md: no YAML frontmatter" in found
    assert "user-only" not in found  # user-only skills need no NOT-clause


def test_long_skill_is_a_warning_not_a_finding(harness):
    (harness / "skills/tdd/SKILL.md").write_text(SKILL.format(name="tdd") + "x\n" * 600)
    assert v.check_skills(harness) == []
    assert "lines > ~500" in v.skill_warnings(harness)[0]


def test_agent_findings(harness):
    (harness / "agents/eng/other.md").write_text(
        AGENT.format(name="worker", model="gpt", skill="ghost")
    )
    (harness / "agents/eng/bare.md").write_text("---\nname: bare\n---\n")
    (harness / "agents/eng/nofm.md").write_text("plain\n")
    found = "\n".join(v.check_agents(harness, {"sonnet"}))
    assert "name 'worker' != filename 'other'" in found
    assert "duplicate agent name 'worker'" in found
    assert "model 'gpt' not in" in found
    assert "preloads skill 'ghost'" in found
    assert "bare.md: missing 'tools'" in found
    assert "nofm.md: no YAML frontmatter" in found


def test_model_registry_drift(harness):
    found = "\n".join(
        v.check_model_registry(harness, {"worker": "opus", "ghost": "haiku"})
    )
    assert "frontmatter model 'sonnet' != models.py DEFAULTS 'opus'" in found
    assert "DEFAULTS lists 'ghost' but no such agent" in found
    assert (
        "missing from orchestrator_engine/models.py"
        in v.check_model_registry(harness, {})[0]
    )


def test_skills_index(harness):
    (harness / "skills/new-one").mkdir()
    (harness / "skills/new-one/SKILL.md").write_text(SKILL.format(name="new-one"))
    agents_md = harness / "AGENTS.md"
    agents_md.write_text(
        agents_md.read_text().replace("| `tdd` | t |", "| `tdd` | t |\n| `gone` | g |")
    )
    found = "\n".join(v.check_skills_index(harness))
    assert "skill 'new-one' missing" in found
    assert "lists 'gone' but skills/gone/ does not exist" in found


def test_links(harness):
    (harness / "docs").mkdir()
    (harness / "docs/a.md").write_text(
        "[ok](b.md) [root](skills/tdd/SKILL.md) [web](https://x.io) [anchor](#h)\n"
        "[dead](missing.md) `skills/ghost/SKILL.md` `skills/<name>/SKILL.md` `docs/adr/`\n"
    )
    (harness / "docs/b.md").write_text("x")
    (harness / "docs/CHANGELOG.md").write_text("[old](gone.md)")
    found = v.check_links(harness)
    assert found == [
        "docs/a.md: broken pointer → missing.md",
        "docs/a.md: broken pointer → skills/ghost/SKILL.md",
    ]


def test_main_exit_codes(harness, capsys):
    (harness / "orchestrator_engine").mkdir()
    (harness / "orchestrator_engine/__init__.py").write_text("")
    (harness / "orchestrator_engine/models.py").write_text(
        'DEFAULTS = {"worker": "sonnet"}\nVALID = {"sonnet"}\n'
    )
    assert v.main([str(harness)]) == 0
    assert "clean" in capsys.readouterr().out
    (harness / "agents/eng/worker.md").write_text(
        AGENT.format(name="worker", model="opus", skill="tdd")
    )
    assert v.main([str(harness)]) == 1
    assert "finding(s)" in capsys.readouterr().err


def test_real_harness_is_clean():
    """The gate: this repo's own agent layer must be wired correctly."""
    assert v.run_all(REPO) == []
