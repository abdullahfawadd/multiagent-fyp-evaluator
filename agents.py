"""Specialist agents for the Lab 09 Hub-and-Spoke multi-agent evaluator."""

from __future__ import annotations

import json
import os
import re
from typing import Any

from dotenv import load_dotenv

from tools import (
    check_existing_systems,
    check_team_scope_fit,
    check_timeline_realism,
    search_literature,
)

try:
    from groq import Groq
except ImportError:  # pragma: no cover - dependency is installed from requirements
    Groq = None  # type: ignore[assignment]


load_dotenv()

DEFAULT_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")


TECH_GENERATOR_PROMPT = """
You are the Technical Reviewer specialist in a multi-agent FYP evaluator.
Use the Reflection pattern generator role. Evaluate only technical merit from
the provided title, technical description, and stack. Do not infer timeline,
team capacity, feasibility, novelty, or ethics. Return a concise but useful
assessment with verdict, strengths, weaknesses, and recommendations.
"""

TECH_CRITIC_PROMPT = """
You are the critic for the Technical Reviewer Reflection loop.
Check whether the assessment is specific, technically grounded, and avoids
timeline/novelty/ethics judgments. If it is ready, start with exactly
ASSESSMENT APPROVED. Otherwise give concrete revision notes.
"""

ETHICS_GENERATOR_PROMPT = """
You are the Ethics and Responsible AI Reviewer specialist in a multi-agent FYP
evaluator. Use the Reflection pattern generator role. Evaluate data privacy,
potential misuse or harm, fairness and bias, Pakistan-specific ethical and
regulatory considerations, and responsible AI compliance. You only receive the
problem statement and technical description. Return a structured review and
include a line in the form RISK_LEVEL: LOW, MEDIUM, or HIGH.
"""

ETHICS_CRITIC_PROMPT = """
You are the critic for the Ethics Reviewer Reflection loop. Check whether the
review covers privacy, misuse/harm, fairness/bias, Pakistan-specific concerns,
and responsible AI safeguards. If it is ready, start with exactly ASSESSMENT
APPROVED. Otherwise give concrete revision notes.
"""

NOVELTY_TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_literature",
            "description": "Search a simulated academic literature database for prior work.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "string",
                        "description": "Search keywords derived from the FYP title and problem statement.",
                    }
                },
                "required": ["keywords"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_existing_systems",
            "description": "Check a simulated production systems database for similar deployed systems.",
            "parameters": {
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "The application domain or product category to check.",
                    }
                },
                "required": ["domain"],
            },
        },
    },
]


def _groq_client() -> Any | None:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or Groq is None:
        return None
    return Groq(api_key=api_key)


def _chat_text(
    messages: list[dict[str, Any]],
    fallback: str,
    *,
    temperature: float = 0.2,
    max_tokens: int = 900,
) -> str:
    client = _groq_client()
    if client is None:
        return fallback
    try:
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content
        return content.strip() if content else fallback
    except Exception as exc:  # pragma: no cover - depends on live API/network
        return f"{fallback}\n\n[Fallback note: Groq call failed: {type(exc).__name__}]"


def _extract_risk_level(text: str) -> str:
    match = re.search(r"RISK[_\s-]*LEVEL\s*:\s*(LOW|MEDIUM|HIGH)", text, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    lowered = text.lower()
    if any(word in lowered for word in ["facial", "surveillance", "biometric", "monitoring", "scrape"]):
        return "HIGH"
    if any(word in lowered for word in ["personal data", "student data", "location", "privacy"]):
        return "MEDIUM"
    return "LOW"


def _technical_fallback(proposal_text: str, revised: bool = False) -> str:
    lowered = proposal_text.lower()
    if "python" in lowered and len(proposal_text) < 130:
        verdict = "WEAK"
        concern = "The technical plan is underspecified and does not name architecture, data, evaluation, or deployment details."
    elif any(term in lowered for term in ["convlstm", "tensorflow", "satellite", "fastapi", "react", "aws"]):
        verdict = "STRONG"
        concern = "The stack is coherent and maps well to the proposed AI and dashboard workflow."
    else:
        verdict = "MODERATE"
        concern = "The project is technically plausible, but needs more detail about data flow and evaluation."

    revision_note = " The revised assessment adds clearer risks and implementation recommendations." if revised else ""
    return (
        f"VERDICT: {verdict}\n"
        f"Strengths: The proposal names an implementable software direction and gives enough stack context for an initial review.\n"
        f"Concerns: {concern}\n"
        f"Recommendations: Define architecture, dataset/source, model or algorithm choice, evaluation metrics, and deployment plan.{revision_note}"
    )


def _technical_critic_fallback(assessment: str) -> str:
    if "VERDICT: WEAK" in assessment and "evaluation" not in assessment.lower():
        return "Needs revision: mention missing evaluation details and architecture risks."
    return "ASSESSMENT APPROVED: The technical assessment is specific and stays within technical scope."


def _ethics_fallback(proposal_text: str, revised: bool = False) -> str:
    risk_level = _extract_risk_level(proposal_text)
    lowered = proposal_text.lower()
    concerns: list[str] = []
    if any(term in lowered for term in ["facial", "biometric", "surveillance", "monitoring"]):
        concerns.append("biometric surveillance can harm privacy, consent, and freedom of movement")
    if any(term in lowered for term in ["student", "university", "social media"]):
        concerns.append("student or social media data requires consent, minimization, and retention limits")
    if any(term in lowered for term in ["ai", "ml", "recognition", "classification"]):
        concerns.append("model bias and false positives must be tested across relevant local groups")
    if not concerns:
        concerns.append("standard privacy, fairness, and transparency safeguards should be documented")

    revision_note = " The revised review explicitly adds responsible AI controls." if revised else ""
    return (
        f"RISK_LEVEL: {risk_level}\n"
        f"Privacy: {concerns[0]}.\n"
        "Misuse/Harm: The proposal should prevent unauthorized repurposing and define human oversight.\n"
        "Fairness/Bias: The team should test performance across gender, language, region, and lighting or context variations where relevant.\n"
        "Pakistan-specific considerations: Align with local institutional approvals, consent expectations, and the Personal Data Protection Bill direction.\n"
        f"Responsible AI safeguards: Use data minimization, consent notices, access controls, audit logs, and a manual appeal process.{revision_note}"
    )


def _ethics_critic_fallback(assessment: str) -> str:
    required = ["privacy", "misuse", "fairness", "pakistan", "safeguards"]
    if all(item in assessment.lower() for item in required):
        return "ASSESSMENT APPROVED: The ethics review covers privacy, harm, fairness, Pakistan-specific context, and safeguards."
    return "Needs revision: cover privacy, misuse/harm, fairness, Pakistan-specific context, and responsible AI safeguards."


def run_technical_reviewer(proposal_text: str) -> dict[str, Any]:
    """Technical specialist using the Reflection pattern."""

    assessment = _chat_text(
        [
            {"role": "system", "content": TECH_GENERATOR_PROMPT},
            {"role": "user", "content": proposal_text},
        ],
        _technical_fallback(proposal_text),
    )

    critic_approved = False
    critiques: list[str] = []
    rounds_taken = 0
    for round_number in range(1, 3):
        critique = _chat_text(
            [
                {"role": "system", "content": TECH_CRITIC_PROMPT},
                {
                    "role": "user",
                    "content": f"Proposal section:\n{proposal_text}\n\nAssessment:\n{assessment}",
                },
            ],
            _technical_critic_fallback(assessment),
            max_tokens=500,
        )
        critiques.append(critique)
        rounds_taken = round_number
        if "ASSESSMENT APPROVED" in critique.upper():
            critic_approved = True
            break
        assessment = _chat_text(
            [
                {"role": "system", "content": TECH_GENERATOR_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Revise the technical assessment.\nProposal section:\n{proposal_text}\n\n"
                        f"Previous assessment:\n{assessment}\n\nCritique:\n{critique}"
                    ),
                },
            ],
            _technical_fallback(proposal_text, revised=True),
        )

    return {
        "agent": "technical_reviewer",
        "pattern": "Reflection",
        "assessment": assessment,
        "reflection_rounds": rounds_taken,
        "critic_approved": critic_approved,
        "critic_notes": critiques,
    }


def _run_novelty_fallback(title: str, problem_statement: str) -> dict[str, Any]:
    literature = search_literature(f"{title} {problem_statement}")
    systems = check_existing_systems(title)
    novelty = literature["novelty_indicator"]
    assessment = (
        f"NOVELTY VERDICT: {novelty}\n"
        f"Literature evidence: {literature['gap_analysis']}\n"
        f"Existing systems: {systems['gap_analysis']}\n"
        "Recommendation: State the unique local dataset, evaluation method, and measurable research contribution."
    )
    return {
        "agent": "novelty_assessor",
        "pattern": "Tool Use",
        "assessment": assessment,
        "tools_called": ["search_literature", "check_existing_systems"],
        "tool_results": [
            {"tool": "search_literature", "result": literature},
            {"tool": "check_existing_systems", "result": systems},
        ],
    }


def _execute_novelty_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "search_literature":
        return search_literature(str(arguments.get("keywords", "")))
    if name == "check_existing_systems":
        return check_existing_systems(str(arguments.get("domain", "")))
    return {"error": f"Unknown tool: {name}"}


def run_novelty_assessor(title: str, problem_statement: str) -> dict[str, Any]:
    """Novelty specialist using the Tool Use pattern."""

    client = _groq_client()
    if client is None:
        return _run_novelty_fallback(title, problem_statement)

    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": (
                "You are the Novelty Assessor in a multi-agent FYP evaluator. "
                "You only receive title and problem statement. You must call both tools: "
                "search_literature and check_existing_systems before writing a concise novelty assessment."
            ),
        },
        {
            "role": "user",
            "content": f"Title: {title}\nProblem statement: {problem_statement}",
        },
    ]
    tools_called: list[str] = []
    tool_results: list[dict[str, Any]] = []

    try:
        for _ in range(5):
            response = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=messages,
                tools=NOVELTY_TOOL_SCHEMAS,
                tool_choice="auto",
                temperature=0.2,
                max_tokens=900,
            )
            message = response.choices[0].message
            tool_calls = message.tool_calls or []
            if not tool_calls:
                content = message.content or "No novelty assessment returned."
                return {
                    "agent": "novelty_assessor",
                    "pattern": "Tool Use",
                    "assessment": content.strip(),
                    "tools_called": tools_called,
                    "tool_results": tool_results,
                }

            assistant_tool_calls = []
            for call in tool_calls:
                assistant_tool_calls.append(
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments or "{}",
                        },
                    }
                )
            messages.append(
                {
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": assistant_tool_calls,
                }
            )

            for call in tool_calls:
                args = json.loads(call.function.arguments or "{}")
                result = _execute_novelty_tool(call.function.name, args)
                tools_called.append(call.function.name)
                tool_results.append({"tool": call.function.name, "arguments": args, "result": result})
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "name": call.function.name,
                        "content": json.dumps(result),
                    }
                )
    except Exception:  # pragma: no cover - depends on live API/network
        return _run_novelty_fallback(title, problem_statement)

    fallback = _run_novelty_fallback(title, problem_statement)
    fallback["assessment"] += "\n[Fallback note: Tool-use loop exhausted before a final answer.]"
    return fallback


def run_feasibility_analyst(
    proposed_months: int,
    team_size: int,
    deliverables_count: int,
    scope_description: str,
) -> dict[str, Any]:
    """Feasibility specialist using an explicit ReAct trace."""

    timeline = check_timeline_realism(proposed_months, deliverables_count, scope_description)
    team = check_team_scope_fit(team_size, scope_description)
    trace = [
        "THOUGHT: I should first test whether the timeline fits the stated deliverables and scope.",
        (
            "ACTION: check_timeline_realism("
            f"proposed_months={proposed_months}, deliverables_count={deliverables_count}, "
            f"scope_description={scope_description!r})"
        ),
        f"OBSERVATION: {json.dumps(timeline)}",
        "THOUGHT: I should now test whether the team size can handle the scope complexity.",
        f"ACTION: check_team_scope_fit(team_size={team_size}, scope_description={scope_description!r})",
        f"OBSERVATION: {json.dumps(team)}",
    ]
    if timeline["verdict"] == "UNREALISTIC" or team["verdict"] == "INSUFFICIENT":
        verdict = "RISKY"
    elif timeline["verdict"] == "TIGHT" or team["verdict"] == "BORDERLINE":
        verdict = "MODERATE RISK"
    else:
        verdict = "FEASIBLE"

    fallback_final = (
        f"FINAL ANSWER: {verdict}. Timeline verdict is {timeline['verdict']} "
        f"and team-scope verdict is {team['verdict']}. {timeline['explanation']} {team['explanation']}"
    )
    final_answer = _chat_text(
        [
            {
                "role": "system",
                "content": (
                    "You are the Feasibility Analyst. Convert the ReAct observations into a concise "
                    "feasibility verdict. Do not discuss technical novelty or ethics."
                ),
            },
            {"role": "user", "content": "\n".join(trace)},
        ],
        fallback_final,
        max_tokens=500,
    )
    trace.append(f"THOUGHT: I have both observations and can now produce the final feasibility verdict.")
    trace.append(final_answer if final_answer.startswith("FINAL ANSWER") else f"FINAL ANSWER: {final_answer}")

    return {
        "agent": "feasibility_analyst",
        "pattern": "ReAct",
        "verdict": verdict,
        "assessment": trace[-1],
        "react_turns": 2,
        "reasoning_trace": trace,
        "tool_results": {
            "timeline_realism": timeline,
            "team_scope_fit": team,
        },
    }


def run_ethics_reviewer(proposal_text: str) -> dict[str, Any]:
    """Ethics specialist using the Reflection pattern."""

    assessment = _chat_text(
        [
            {"role": "system", "content": ETHICS_GENERATOR_PROMPT},
            {"role": "user", "content": proposal_text},
        ],
        _ethics_fallback(proposal_text),
    )

    critic_approved = False
    critiques: list[str] = []
    rounds_taken = 0
    for round_number in range(1, 3):
        critique = _chat_text(
            [
                {"role": "system", "content": ETHICS_CRITIC_PROMPT},
                {
                    "role": "user",
                    "content": f"Proposal section:\n{proposal_text}\n\nEthics assessment:\n{assessment}",
                },
            ],
            _ethics_critic_fallback(assessment),
            max_tokens=500,
        )
        critiques.append(critique)
        rounds_taken = round_number
        if "ASSESSMENT APPROVED" in critique.upper():
            critic_approved = True
            break
        assessment = _chat_text(
            [
                {"role": "system", "content": ETHICS_GENERATOR_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Revise the ethics assessment.\nProposal section:\n{proposal_text}\n\n"
                        f"Previous assessment:\n{assessment}\n\nCritique:\n{critique}"
                    ),
                },
            ],
            _ethics_fallback(proposal_text, revised=True),
        )

    return {
        "agent": "ethics_reviewer",
        "pattern": "Reflection",
        "assessment": assessment,
        "risk_level": _extract_risk_level(assessment + "\n" + proposal_text),
        "reflection_rounds": rounds_taken,
        "critic_approved": critic_approved,
        "critic_notes": critiques,
    }


def call_orchestrator_llm(prompt: str, fallback: str) -> str:
    """Shared LLM call for orchestrator synthesis."""

    return _chat_text(
        [
            {
                "role": "system",
                "content": (
                    "You are the orchestrator synthesis component. You do not perform domain review. "
                    "You only combine specialist reports, surface conflicts, and produce a final evaluation."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        fallback,
        temperature=0.15,
        max_tokens=1200,
    )
