"""Pure simulated tools used by the Lab 09 specialist agents."""

from __future__ import annotations

import re
from typing import Any


def _tokens(text: str) -> set[str]:
    return {token.lower() for token in re.findall(r"[a-zA-Z0-9]+", text)}


def _complexity_score(scope_description: str, deliverables_count: int = 0) -> int:
    text = scope_description.lower()
    score = max(1, deliverables_count)
    high_complexity_terms = [
        "ai",
        "ml",
        "deep learning",
        "computer vision",
        "real time",
        "satellite",
        "iot",
        "blockchain",
        "federated",
        "mobile",
        "dashboard",
        "cloud",
        "deployment",
        "privacy",
        "biometric",
    ]
    for term in high_complexity_terms:
        if term in text:
            score += 1
    return min(score, 10)


def search_literature(keywords: str) -> dict[str, Any]:
    """Simulate an academic literature lookup for the Novelty Assessor."""

    keyword_tokens = _tokens(keywords)
    joined = " ".join(sorted(keyword_tokens))

    if {"chatbot", "university"} & keyword_tokens:
        papers = [
            "Campus FAQ Chatbots Using Retrieval-Augmented Generation (2023)",
            "Student Services Virtual Assistants: A Systematic Review (2022)",
            "Intent Classification for University Helpdesks (2021)",
        ]
        novelty = "LOW"
        gap = "Many academic and production systems already solve general university FAQ support."
    elif {"cloudburst", "flood", "kpk", "satellite"} & keyword_tokens:
        papers = [
            "Satellite Rainfall Nowcasting for Mountainous Regions (2022)",
            "Deep Learning for Flash Flood Early Warning in South Asia (2023)",
        ]
        novelty = "MEDIUM_HIGH"
        gap = "There is related work, but a KPK-specific satellite early warning pipeline remains a defensible gap."
    elif {"facial", "recognition", "surveillance", "monitoring"} & keyword_tokens:
        papers = [
            "Face Recognition Attendance Systems in Universities (2020)",
            "Privacy Risks in Automated Surveillance (2022)",
        ]
        novelty = "LOW_MEDIUM"
        gap = "The technical area is mature; novelty depends on governance, privacy safeguards, or a narrow local use case."
    else:
        papers = [
            f"Search result for '{joined[:48] or 'general fyp topic'}' in applied computing venues",
            "Recent student capstone projects with overlapping implementation patterns",
        ]
        novelty = "MEDIUM"
        gap = "The proposal may be novel if it states a clear local dataset, target population, or evaluation method."

    return {
        "query": keywords,
        "found_papers": papers,
        "novelty_indicator": novelty,
        "gap_analysis": gap,
    }


def check_existing_systems(domain: str) -> dict[str, Any]:
    """Simulate a production systems lookup for the Novelty Assessor."""

    text = domain.lower()
    if "chatbot" in text:
        systems = ["Google Dialogflow FAQ bots", "Intercom Fin", "University helpdesk chatbots"]
        gap = "A generic chatbot is not enough; needs a specific dataset, workflow integration, or evaluation contribution."
    elif "cloudburst" in text or "flood" in text:
        systems = ["PMD weather alerts", "NASA GPM flood monitoring dashboards", "Global Flood Awareness System"]
        gap = "Existing systems are broad; localized KPK prediction and student-built dashboard integration can be differentiated."
    elif "face" in text or "facial" in text or "surveillance" in text:
        systems = ["Commercial face recognition attendance systems", "CCTV analytics platforms"]
        gap = "Existing systems are common, and ethical risk is high unless consent, minimization, and oversight are central."
    else:
        systems = ["Comparable SaaS products", "Open-source templates", "Prior FYP implementations"]
        gap = "The proposal needs a sharper user group, evaluation plan, and differentiating feature."

    return {
        "domain": domain,
        "known_systems": systems,
        "gap_analysis": gap,
    }


def check_timeline_realism(
    proposed_months: int,
    deliverables_count: int,
    scope_description: str,
) -> dict[str, Any]:
    """Assess whether the proposed timeline fits the apparent project complexity."""

    complexity_score = _complexity_score(scope_description, deliverables_count)
    min_months_needed = max(3, round(complexity_score * 1.25))
    if proposed_months >= min_months_needed + 2:
        verdict = "REALISTIC"
        explanation = "The timeline has useful buffer for implementation, evaluation, and documentation."
    elif proposed_months >= min_months_needed:
        verdict = "TIGHT"
        explanation = "The project can fit, but only with disciplined scope control and early prototyping."
    else:
        verdict = "UNREALISTIC"
        explanation = "The timeline is shorter than the estimated minimum for the stated scope."

    return {
        "proposed_months": proposed_months,
        "deliverables_count": deliverables_count,
        "complexity_score": complexity_score,
        "min_months_needed": min_months_needed,
        "verdict": verdict,
        "explanation": explanation,
    }


def check_team_scope_fit(team_size: int, scope_description: str) -> dict[str, Any]:
    """Assess whether the team size is enough for the scope."""

    complexity_score = _complexity_score(scope_description)
    team_capacity = max(1, team_size) * 2
    if team_capacity >= complexity_score + 2:
        verdict = "ADEQUATE"
        explanation = "The team size appears sufficient if responsibilities are divided clearly."
    elif team_capacity >= complexity_score:
        verdict = "BORDERLINE"
        explanation = "The team can attempt the scope, but should reduce optional features."
    else:
        verdict = "INSUFFICIENT"
        explanation = "The scope is too broad for the team size without major simplification."

    return {
        "team_size": team_size,
        "scope_complexity_score": complexity_score,
        "team_capacity": team_capacity,
        "verdict": verdict,
        "explanation": explanation,
    }
