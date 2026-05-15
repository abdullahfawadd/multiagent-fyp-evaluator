# Lab 09 Submission Notes

## Verification Checklist

- `GET /health` shows the orchestrator plus four specialists, including `ethics_reviewer`.
- `POST /evaluate` returns `execution_mode: sequential`.
- `POST /evaluate/parallel` returns `execution_mode: parallel`.
- `specialist_reports.technical_reviewer.reflection_rounds` is present.
- `specialist_reports.novelty_assessor.tools_called` includes `search_literature` and `check_existing_systems`.
- `specialist_reports.feasibility_analyst.reasoning_trace` includes THOUGHT, ACTION, OBSERVATION, and FINAL ANSWER lines.
- `specialist_reports.ethics_reviewer.risk_level` is present.
- `n8n_workflows/academic_paper_multiagent.json` is valid JSON.

## Timing Comparison

Local verification timings from this workspace, using the built-in fallback path because no `.env` key was committed:

- Sequential `/evaluate`: `0.001` seconds
- Parallel `/evaluate/parallel`: `0.003` seconds
- Speedup ratio: `0.001 / 0.003 = 0.33`

These fallback timings only prove endpoint behavior. For the lab demo, add `GROQ_API_KEY` to local `.env`, rerun both endpoints with the strong proposal, and replace the numbers above with live Groq timings. If Groq free-tier rate limits slow the parallel endpoint, mention that parallelism is bounded by the slowest shared external dependency.

## Ethics Specialist Demonstration Proposal

Use `ethics_risk_proposal` from `test_proposals.json`. It should trigger a substantive ethics review because it includes facial recognition, biometric templates, CCTV streams, and student monitoring.

## Reflection Question

Adding the Ethics Reviewer shows that Hub-and-Spoke separates specialist concerns from orchestration logic. The three existing specialists did not need to know that a new reviewer existed, because each specialist remains isolated behind its own function and output contract. The orchestrator is the only layer that changes when a new domain perspective is added. This makes the architecture easier to extend, debug, and test because new expertise can be added without rewriting existing agents. In a production document review pipeline, this is commercially important because a company can add new compliance, risk, or jurisdiction specialists as customer requirements change. It reduces delivery risk and lets teams sell modular review capabilities without rebuilding the whole system.
