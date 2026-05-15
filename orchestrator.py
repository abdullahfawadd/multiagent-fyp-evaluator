"""Sequential orchestration for the Hub-and-Spoke multi-agent evaluator."""

from __future__ import annotations

import json
import time
from typing import Any

from agents import (
    call_orchestrator_llm,
    run_ethics_reviewer,
    run_feasibility_analyst,
    run_novelty_assessor,
    run_technical_reviewer,
)


ORCHESTRATOR_SYNTHESIS_PROMPT = """
You are the Orchestrator in a Hub-and-Spoke multi-agent FYP evaluator.
You never do domain work yourself. Use only the provided specialist reports.

Synthesize:
1. Overall verdict
2. Top strengths
3. Top 3 concerns
4. Recommendations
5. Notable conflicts between specialists

If the Ethics Reviewer flags HIGH risk, include ethics in the Top 3 concerns.
"""


def extract_proposal_sections(proposal: dict[str, Any]) -> dict[str, Any]:
    """Implement agent isolation by sharing only task-relevant fields."""

    title = proposal["title"]
    problem_statement = proposal["problem_statement"]
    technical_description = proposal["technical_description"]
    technology_stack = proposal["technology_stack"]

    return {
        "technical": (
            f"Title: {title}\n"
            f"Technical description: {technical_description}\n"
            f"Technology stack: {technology_stack}"
        ),
        "novelty_title": title,
        "novelty_problem": problem_statement,
        "feasibility_months": proposal["proposed_months"],
        "feasibility_team": proposal["team_size"],
        "feasibility_deliverables": proposal["deliverables_count"],
        "feasibility_scope": (
            f"Title: {title}. Scope: {technical_description}. "
            f"Deliverables count: {proposal['deliverables_count']}."
        ),
        "ethics": (
            f"Problem statement: {problem_statement}\n"
            f"Technical description: {technical_description}"
        ),
    }


def _contains_any(text: str, words: list[str]) -> bool:
    lowered = text.lower()
    return any(word in lowered for word in words)


def detect_conflicts(specialist_reports: dict[str, Any]) -> list[dict[str, str]]:
    """Surface disagreements without averaging them away."""

    conflicts: list[dict[str, str]] = []
    technical_text = json.dumps(specialist_reports.get("technical_reviewer", {})).lower()
    novelty_text = json.dumps(specialist_reports.get("novelty_assessor", {})).lower()
    feasibility_text = json.dumps(specialist_reports.get("feasibility_analyst", {})).lower()
    ethics_report = specialist_reports.get("ethics_reviewer", {})
    ethics_risk = str(ethics_report.get("risk_level", "")).upper()

    technical_positive = _contains_any(
        technical_text,
        ["strong", "promising", "robust", "coherent", "excellent", "technically feasible"],
    )
    feasibility_negative = _contains_any(
        feasibility_text,
        ["unrealistic", "insufficient", "risky", "tight", "moderate risk"],
    )
    novelty_low = _contains_any(novelty_text, ["novelty verdict: low", "low", "common", "many existing"])

    if technical_positive and feasibility_negative:
        conflicts.append(
            {
                "type": "technical_feasibility_conflict",
                "description": "Technical design appears promising, but feasibility analysis reports timeline or team risk.",
            }
        )
    if technical_positive and novelty_low:
        conflicts.append(
            {
                "type": "technical_novelty_conflict",
                "description": "Technical implementation may be solid, but novelty appears weak or already well served.",
            }
        )
    if technical_positive and ethics_risk == "HIGH":
        conflicts.append(
            {
                "type": "technical_ethics_conflict",
                "description": "Technical reviewer is positive while the Ethics Reviewer flags high responsible-AI risk.",
            }
        )

    return conflicts


def _fallback_synthesis(
    specialist_reports: dict[str, Any],
    conflicts: list[dict[str, str]],
) -> str:
    feasibility = specialist_reports["feasibility_analyst"].get("verdict", "UNKNOWN")
    ethics = specialist_reports["ethics_reviewer"].get("risk_level", "UNKNOWN")
    novelty = specialist_reports["novelty_assessor"].get("assessment", "")

    if ethics == "HIGH":
        verdict = "CONDITIONALLY ACCEPT WITH MAJOR ETHICS REVISIONS"
    elif "LOW" in novelty.upper():
        verdict = "REVISE FOR NOVELTY"
    elif feasibility in {"RISKY", "MODERATE RISK"}:
        verdict = "REVISE BEFORE APPROVAL"
    else:
        verdict = "PROMISING"

    conflict_lines = "\n".join(f"- {item['description']}" for item in conflicts) or "- No major conflicts detected."
    return (
        f"Overall verdict: {verdict}\n"
        "Top strengths:\n"
        "- Specialist reports provide separate technical, novelty, feasibility, and ethics perspectives.\n"
        "- The proposal can improve quickly if the team acts on the targeted recommendations.\n"
        "Top 3 concerns:\n"
        f"- Ethics risk level: {ethics}.\n"
        f"- Feasibility verdict: {feasibility}.\n"
        "- Novelty and evaluation evidence must be made explicit.\n"
        "Recommendations:\n"
        "- Narrow the scope, define measurable evaluation criteria, and document safeguards before implementation.\n"
        "Notable conflicts:\n"
        f"{conflict_lines}"
    )


def synthesize_evaluation(
    proposal: dict[str, Any],
    specialist_reports: dict[str, Any],
    conflicts: list[dict[str, str]],
) -> str:
    prompt = (
        f"{ORCHESTRATOR_SYNTHESIS_PROMPT}\n\n"
        f"Proposal title: {proposal['title']}\n\n"
        f"Specialist reports JSON:\n{json.dumps(specialist_reports, indent=2)}\n\n"
        f"Conflicts JSON:\n{json.dumps(conflicts, indent=2)}"
    )
    return call_orchestrator_llm(prompt, _fallback_synthesis(specialist_reports, conflicts))


def evaluate_proposal(proposal: dict[str, Any]) -> dict[str, Any]:
    start = time.perf_counter()
    sections = extract_proposal_sections(proposal)

    tech_report = run_technical_reviewer(sections["technical"])
    novelty_report = run_novelty_assessor(sections["novelty_title"], sections["novelty_problem"])
    feasibility_report = run_feasibility_analyst(
        sections["feasibility_months"],
        sections["feasibility_team"],
        sections["feasibility_deliverables"],
        sections["feasibility_scope"],
    )
    ethics_report = run_ethics_reviewer(sections["ethics"])

    specialist_reports = {
        "technical_reviewer": tech_report,
        "novelty_assessor": novelty_report,
        "feasibility_analyst": feasibility_report,
        "ethics_reviewer": ethics_report,
    }
    conflicts = detect_conflicts(specialist_reports)
    final_evaluation = synthesize_evaluation(proposal, specialist_reports, conflicts)

    return {
        "execution_mode": "sequential",
        "execution_time_s": round(time.perf_counter() - start, 3),
        "specialist_reports": specialist_reports,
        "conflicts_detected": conflicts,
        "final_evaluation": final_evaluation,
    }
