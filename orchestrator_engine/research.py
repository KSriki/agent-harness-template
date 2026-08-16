"""create_research_plan / format_research_summary — structure around research dispatch."""

from __future__ import annotations

TREND_WORDS = ("trend", "latest", "ecosystem", "what changed", "new in", "state of")


def create_research_plan(questions: list[str]) -> dict:
    """Route each question to the right research agent, deterministically."""
    plan = []
    for i, q in enumerate(questions, 1):
        agent = "trend-scout" if any(w in q.lower() for w in TREND_WORDS) else "debug-research"
        plan.append({"id": i, "question": q, "agent": agent, "status": "pending"})
    return {"questions": plan, "note": "dispatch in parallel; each returns its skill's output contract"}


def format_research_summary(findings: list[dict]) -> str:
    """findings: [{"question","verdict","confidence","sources": [..]}] -> markdown."""
    lines = ["| # | Question | Verdict | Confidence | Sources |", "|---|---|---|---|---|"]
    for i, f in enumerate(findings, 1):
        sources = " · ".join(f.get("sources", [])) or "—"
        lines.append(
            f"| {i} | {f.get('question','?')} | {f.get('verdict','?')} | {f.get('confidence','?')} | {sources} |"
        )
    return "\n".join(lines) + "\n"
