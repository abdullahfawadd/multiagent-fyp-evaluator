# Multi-Agent FYP Evaluator

Lab 09 implementation for **Agentic AI Design Patterns: Multi-Agent Pattern**.

The app uses a Hub-and-Spoke architecture:

- Orchestrator: coordination, conflict detection, and synthesis only
- Technical Reviewer: Reflection pattern
- Novelty Assessor: Tool Use pattern
- Feasibility Analyst: ReAct pattern
- Ethics Reviewer: Reflection pattern for responsible AI

## Setup

```powershell
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Add your Groq key to `.env`:

```text
GROQ_API_KEY=your_groq_key_here
GROQ_MODEL=llama-3.1-8b-instant
```

`.env` is ignored by Git and should never be committed.

## Run

```powershell
uvicorn main:app --reload --port 8000
```

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Sequential evaluation:

```powershell
$body = Get-Content .\test_proposals.json | ConvertFrom-Json
$json = $body.strong_proposal | ConvertTo-Json -Depth 10
Invoke-RestMethod http://127.0.0.1:8000/evaluate -Method Post -ContentType "application/json" -Body $json
```

Parallel evaluation:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/evaluate/parallel -Method Post -ContentType "application/json" -Body $json
```

## n8n Workflow

The exported Academic Paper multi-agent workflow is in:

```text
n8n_workflows/academic_paper_multiagent.json
```

Set `GROQ_API_KEY` in the n8n environment before running the workflow.
