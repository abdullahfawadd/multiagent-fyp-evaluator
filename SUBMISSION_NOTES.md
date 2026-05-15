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

Live verification timings from this workspace after adding `GROQ_API_KEY` to local ignored `.env`:

- Sequential `/evaluate`: `55.094` seconds
- Parallel `/evaluate/parallel`: `61.125` seconds
- Speedup ratio: `55.094 / 61.125 = 0.90`

The direct Groq API key check passed. In this run, parallel mode was not faster because the Groq free-tier/shared external dependency became the bottleneck during many LLM calls. This is valid to explain in the lab demo: parallelism is bounded by the slowest and most rate-limited dependency.

## Ethics Specialist Demonstration Proposal

Use `ethics_risk_proposal` from `test_proposals.json`. It should trigger a substantive ethics review because it includes facial recognition, biometric templates, CCTV streams, and student monitoring.

## Reflection Question

Adding the Ethics Reviewer shows that Hub-and-Spoke separates specialist concerns from orchestration logic. The three existing specialists did not need to know that a new reviewer existed, because each specialist remains isolated behind its own function and output contract. The orchestrator is the only layer that changes when a new domain perspective is added. This makes the architecture easier to extend, debug, and test because new expertise can be added without rewriting existing agents. In a production document review pipeline, this is commercially important because a company can add new compliance, risk, or jurisdiction specialists as customer requirements change. It reduces delivery risk and lets teams sell modular review capabilities without rebuilding the whole system.
