"""FastAPI entrypoint for Lab 09 Multi-Agent FYP Evaluator."""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from orchestrator import evaluate_proposal
from orchestrator_async import evaluate_proposal_parallel


app = FastAPI(
    title="Lab 09 Multi-Agent FYP Evaluator",
    description="Hub-and-Spoke multi-agent evaluator using Groq and FastAPI.",
    version="1.0.0",
)


class ProposalRequest(BaseModel):
    title: str = Field(..., min_length=3)
    problem_statement: str = Field(..., min_length=5)
    technical_description: str = Field(..., min_length=5)
    technology_stack: str = Field(..., min_length=2)
    proposed_months: int = Field(..., ge=1, le=24)
    team_size: int = Field(..., ge=1, le=8)
    deliverables_count: int = Field(..., ge=1, le=20)


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "architecture": "Hub and Spoke - Orchestrator + 4 Specialists",
        "agents": {
            "orchestrator": "Coordination and synthesis only - no domain work",
            "technical_reviewer": "Reflection pattern (Lab 07)",
            "novelty_assessor": "Tool Use pattern (Lab 08)",
            "feasibility_analyst": "ReAct pattern (Lab 06)",
            "ethics_reviewer": "Reflection pattern for Responsible AI review",
        },
    }


@app.post("/evaluate")
def evaluate(request: ProposalRequest) -> dict[str, object]:
    return evaluate_proposal(request.model_dump())


@app.post("/evaluate/parallel")
async def evaluate_parallel(request: ProposalRequest) -> dict[str, object]:
    return await evaluate_proposal_parallel(request.model_dump())
