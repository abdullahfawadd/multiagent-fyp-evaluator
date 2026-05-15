"""Parallel orchestration for the Hub-and-Spoke multi-agent evaluator."""

from __future__ import annotations

import asyncio
import functools
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

from agents import (
    run_ethics_reviewer,
    run_feasibility_analyst,
    run_novelty_assessor,
    run_technical_reviewer,
)
from orchestrator import detect_conflicts, extract_proposal_sections, synthesize_evaluation


_EXECUTOR = ThreadPoolExecutor(max_workers=4)


async def run_agent_async(func: Callable[..., Any], *args: Any) -> Any:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_EXECUTOR, functools.partial(func, *args))


async def evaluate_proposal_parallel(proposal: dict[str, Any]) -> dict[str, Any]:
    start = time.perf_counter()
    sections = extract_proposal_sections(proposal)

    tech_report, novelty_report, feasibility_report, ethics_report = await asyncio.gather(
        run_agent_async(run_technical_reviewer, sections["technical"]),
        run_agent_async(run_novelty_assessor, sections["novelty_title"], sections["novelty_problem"]),
        run_agent_async(
            run_feasibility_analyst,
            sections["feasibility_months"],
            sections["feasibility_team"],
            sections["feasibility_deliverables"],
            sections["feasibility_scope"],
        ),
        run_agent_async(run_ethics_reviewer, sections["ethics"]),
    )

    specialist_reports = {
        "technical_reviewer": tech_report,
        "novelty_assessor": novelty_report,
        "feasibility_analyst": feasibility_report,
        "ethics_reviewer": ethics_report,
    }
    conflicts = detect_conflicts(specialist_reports)
    final_evaluation = await run_agent_async(synthesize_evaluation, proposal, specialist_reports, conflicts)

    return {
        "execution_mode": "parallel",
        "execution_time_s": round(time.perf_counter() - start, 3),
        "specialist_reports": specialist_reports,
        "conflicts_detected": conflicts,
        "final_evaluation": final_evaluation,
    }
