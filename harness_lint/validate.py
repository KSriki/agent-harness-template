"""The checks. Each returns a list of human-readable findings ("" = none).

What each one catches — every check exists because its failure shipped once:
- frontmatter      → a skill/agent that never loads or never routes (missing name/description,
                     name ≠ dir, no NOT-clause so it collides with its neighbour)
- preloads         → an agent preloading a skill that doesn't exist
- model registry   → orchestrator_engine.models.DEFAULTS drifting from agent frontmatter
                     (premise-reviewer shipped missing from DEFAULTS → silently ran on inherit)
- skills index     → a skill absent from the AGENTS.md table is invisible to routing
- links            → a pointer to a file that doesn't exist (a skill citing a missing doc)
"""

from __future__ import annotations

import re
import runpy
import sys
from pathlib import Path

KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_SKILL_LINES = 500
AGENT_REQUIRED = ("name", "description", "tools", "model")
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
# Backticked paths are checked only under the harness-owned trees: `docs/...` in a
# skill usually names a file in the TARGET project (docs/adr/, docs/plans/), not here.
BACKTICK_PATH = re.compile(r"`((?:skills|agents)/[^`\s]+)`")
HISTORICAL = {"CHANGELOG.md"}  # records what WAS true; old paths are expected
PLACEHOLDER = re.compile(r"[<>〈〉*{}$]|\.\.\.|…")


# ── Frontmatter (the YAML subset this repo uses; no PyYAML dependency) ────────


def parse_frontmatter(text: str) -> dict | None:
    """`key: value`, folded/literal blocks (`>` / `|`), and `- item` lists.
    Strips trailing `# comments` from plain scalars. None if no frontmatter."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    try:
        end = lines.index("---", 1)
    except ValueError:
        return None
    data: dict = {}
    key = None
    for line in lines[1:end]:
        m = re.match(r"^([A-Za-z][\w-]*):\s*(.*)$", line)
        if m:
            key, value = m.group(1), _strip_comment(m.group(2))
            if value in (">", "|", ">-", "|-"):
                data[key] = ""
            elif value == "":
                data[key] = []
            else:
                data[key] = value.strip("\"'")
            continue
        stripped = line.strip()
        if key is None or not stripped or stripped.startswith("#"):
            continue
        if isinstance(data[key], list) and stripped.startswith("- "):
            data[key].append(_strip_comment(stripped[2:]).strip("\"'"))
        elif isinstance(data[key], str) and line.startswith((" ", "\t")):
            data[key] = (data[key] + " " + stripped).strip()
    return data


def _strip_comment(value: str) -> str:
    if value.startswith(("'", '"')):
        return value.strip()
    return re.split(r"\s+#", value, maxsplit=1)[0].strip()


# ── Discovery ─────────────────────────────────────────────────────────────────


def skill_files(root: Path) -> list[Path]:
    return sorted(
        p for p in (root / "skills").glob("*/SKILL.md") if p.parent.name != "_TEMPLATE"
    )


def agent_files(root: Path) -> list[Path]:
    return sorted(p for p in (root / "agents").rglob("*.md") if p.name != "README.md")


# ── Checks ────────────────────────────────────────────────────────────────────


def check_skills(root: Path) -> list[str]:
    findings = []
    for path in skill_files(root):
        rel = path.relative_to(root)
        fm = parse_frontmatter(path.read_text())
        if fm is None:
            findings.append(f"{rel}: no YAML frontmatter")
            continue
        name, desc = fm.get("name", ""), fm.get("description", "")
        if name != path.parent.name:
            findings.append(f"{rel}: name '{name}' != directory '{path.parent.name}'")
        if not KEBAB.match(name or "-"):
            findings.append(f"{rel}: name '{name}' is not kebab-case")
        if not desc:
            findings.append(f"{rel}: empty description — the skill can never route")
        elif fm.get("disable-model-invocation") != "true" and "NOT" not in desc:
            findings.append(
                f"{rel}: description has no NOT-clause (house style: triggers + 'Do NOT use for')"
            )
    return findings


def skill_warnings(root: Path) -> list[str]:
    """Advisory only — house style, not wiring. Printed, never fails the gate."""
    warnings = []
    for path in skill_files(root):
        n = len(path.read_text().splitlines())
        if n > MAX_SKILL_LINES:
            warnings.append(
                f"{path.relative_to(root)}: {n} lines > ~{MAX_SKILL_LINES} — consider reference files"
            )
    return warnings


def agent_frontmatter(root: Path) -> dict[str, tuple[Path, dict]]:
    out = {}
    for path in agent_files(root):
        fm = parse_frontmatter(path.read_text()) or {}
        out[fm.get("name") or path.stem] = (path, fm)
    return out


def check_agents(root: Path, valid_models: set[str]) -> list[str]:
    findings = []
    skills = {p.parent.name for p in skill_files(root)}
    seen: dict[str, Path] = {}
    for path in agent_files(root):
        rel = path.relative_to(root)
        fm = parse_frontmatter(path.read_text())
        if fm is None:
            findings.append(f"{rel}: no YAML frontmatter")
            continue
        for key in AGENT_REQUIRED:
            if not fm.get(key):
                findings.append(f"{rel}: missing '{key}'")
        name = fm.get("name", "")
        if name and name != path.stem:
            findings.append(f"{rel}: name '{name}' != filename '{path.stem}'")
        if name in seen:
            findings.append(f"{rel}: duplicate agent name '{name}' (also {seen[name]})")
        seen[name] = rel
        if fm.get("model") and fm["model"] not in valid_models:
            findings.append(
                f"{rel}: model '{fm['model']}' not in {sorted(valid_models)}"
            )
        preload = fm.get("skills", [])
        for skill in [preload] if isinstance(preload, str) else preload:
            if skill not in skills:
                findings.append(f"{rel}: preloads skill '{skill}' which does not exist")
    return findings


def check_model_registry(root: Path, defaults: dict[str, str]) -> list[str]:
    findings = []
    agents = agent_frontmatter(root)
    for name, (path, fm) in agents.items():
        rel = path.relative_to(root)
        if name not in defaults:
            findings.append(
                f"{rel}: '{name}' missing from orchestrator_engine/models.py DEFAULTS"
            )
        elif fm.get("model") and defaults[name] != fm["model"]:
            findings.append(
                f"{rel}: frontmatter model '{fm['model']}' != models.py DEFAULTS '{defaults[name]}'"
            )
    for name in sorted(set(defaults) - set(agents)):
        findings.append(
            f"orchestrator_engine/models.py: DEFAULTS lists '{name}' but no such agent"
        )
    return findings


def check_skills_index(root: Path) -> list[str]:
    agents_md = (root / "AGENTS.md").read_text()
    section = agents_md.split("## Skills available", 1)[-1].split("\n## ", 1)[0]
    indexed = set(re.findall(r"^\|\s*`([a-z0-9-]+)`\s*\|", section, re.M))
    findings = []
    for path in skill_files(root):
        fm = parse_frontmatter(path.read_text()) or {}
        name = path.parent.name
        if fm.get("disable-model-invocation") == "true":
            continue  # user-only skills don't route; they needn't be in the model's table
        if name not in indexed:
            findings.append(
                f"AGENTS.md: skill '{name}' missing from the 'Skills available' table"
            )
    for name in sorted(indexed - {p.parent.name for p in skill_files(root)}):
        findings.append(
            f"AGENTS.md: 'Skills available' lists '{name}' but skills/{name}/ does not exist"
        )
    return findings


def markdown_files(root: Path) -> list[Path]:
    files = [p for p in root.glob("*.md")]
    for sub in ("skills", "agents", "docs", "gates", "evals"):
        files += (root / sub).rglob("*.md")
    return sorted(
        p
        for p in files
        if ".claude" not in p.parts
        and "_TEMPLATE" not in p.parts
        and p.name not in HISTORICAL
    )


def check_links(root: Path) -> list[str]:
    """A pointer resolves if it exists relative to the file OR to the repo root
    (agents read repo-root paths; GitHub renders file-relative ones)."""
    findings = []
    for path in markdown_files(root):
        text = path.read_text()
        targets = [t for t in LINK.findall(text) if not re.match(r"^[a-z]+:|^#", t)]
        targets += BACKTICK_PATH.findall(text)
        for target in dict.fromkeys(targets):
            clean = target.split("#", 1)[0].rstrip("/.,;:")
            if not clean or PLACEHOLDER.search(clean):
                continue
            if not (
                (path.parent / clean).exists() or (root / clean.lstrip("./")).exists()
            ):
                findings.append(f"{path.relative_to(root)}: broken pointer → {target}")
    return findings


def run_all(root: Path) -> list[str]:
    # Load by path, not import: the registry under test is THIS root's, never a cached module.
    models = runpy.run_path(str(root / "orchestrator_engine" / "models.py"))
    DEFAULTS, VALID = models["DEFAULTS"], models["VALID"]
    return (
        check_skills(root)
        + check_agents(root, set(VALID))
        + check_model_registry(root, dict(DEFAULTS))
        + check_skills_index(root)
        + check_links(root)
    )


def main(argv: list[str]) -> int:
    root = Path(argv[0] if argv else ".").resolve()
    findings = run_all(root)
    for w in skill_warnings(root):
        print(f"warning: {w}", file=sys.stderr)
    for f in findings:
        print(f, file=sys.stderr)
    if findings:
        print(f"harness_lint: {len(findings)} finding(s)", file=sys.stderr)
        return 1
    print("harness_lint: clean")
    return 0
