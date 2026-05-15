# Lab 09 Report: Multi-Agent FYP Evaluator

## 1. Lab Title

**Agentic AI Design Patterns: Multi-Agent Pattern**

Project implemented: **FYP Proposal Evaluator using Hub-and-Spoke Multi-Agent Architecture**

Repository: `multiagent-fyp-evaluator`

Backend framework: `FastAPI`

LLM provider: `Groq`

Model: `llama-3.1-8b-instant`

## 2. Objective

The objective of this lab is to implement the Multi-Agent Pattern using a Hub-and-Spoke architecture. The system evaluates Final Year Project proposals by sending isolated proposal sections to specialist agents, then the orchestrator combines their outputs into one final evaluation report.

This implementation includes the base lab system plus the graded fourth specialist:

- Technical Reviewer using the Reflection pattern
- Novelty Assessor using the Tool Use pattern
- Feasibility Analyst using the ReAct pattern
- Ethics and Responsible AI Reviewer using the Reflection pattern
- Sequential evaluation endpoint
- Parallel evaluation endpoint using `asyncio.gather()`
- n8n workflow JSON for a separate Academic Paper Review multi-agent workflow

## 3. Architecture Summary

The system follows the **Hub-and-Spoke** pattern.

The orchestrator is the hub. It receives the full FYP proposal, extracts isolated sections, calls each specialist, detects conflicts, and synthesizes the final report.

The specialists are the spokes. Each specialist only receives the information required for its own task.

```text
                         ORCHESTRATOR
               coordination, conflict detection,
                    final synthesis only
                              |
        -------------------------------------------------
        |                  |                  |          |
Technical Reviewer   Novelty Assessor   Feasibility   Ethics Reviewer
  Reflection           Tool Use            ReAct        Reflection
```

The orchestrator never performs domain work itself. It does not judge technical quality, novelty, feasibility, or ethics directly. It only combines the specialist reports.

## 4. Files Created

| File | Purpose |
| --- | --- |
| `main.py` | FastAPI entrypoint with `/health`, `/evaluate`, and `/evaluate/parallel` |
| `agents.py` | Contains all four specialist agents and the Groq helper |
| `tools.py` | Contains simulated tools used by the Novelty and Feasibility agents |
| `orchestrator.py` | Sequential orchestration, agent isolation, conflict detection, synthesis |
| `orchestrator_async.py` | Parallel orchestration using `asyncio.gather()` |
| `test_proposals.json` | Strong, weak, and ethics-risk sample proposals |
| `requirements.txt` | Python dependencies |
| `.env.example` | Example environment variables without real secrets |
| `.gitignore` | Ensures `.env` and generated files are not committed |
| `README.md` | Quick setup and run instructions |
| `SUBMISSION_NOTES.md` | Checklist, timing comparison, and reflection answer |
| `LAB_REPORT.md` | Detailed report and testing guide |
| `n8n_workflows/academic_paper_multiagent.json` | Exported n8n multi-agent workflow |

## 5. Where the Main Code Is Added

### 5.1 FastAPI Routes

File: `main.py`

Important code:

```python
@app.get("/health")
def health() -> dict[str, object]:
    ...

@app.post("/evaluate")
def evaluate(request: ProposalRequest) -> dict[str, object]:
    return evaluate_proposal(request.model_dump())

@app.post("/evaluate/parallel")
async def evaluate_parallel(request: ProposalRequest) -> dict[str, object]:
    return await evaluate_proposal_parallel(request.model_dump())
```

This file defines the public API used in Postman.

### 5.2 Specialist Agents

File: `agents.py`

Important functions:

```python
run_technical_reviewer(proposal_text)
run_novelty_assessor(title, problem_statement)
run_feasibility_analyst(proposed_months, team_size, deliverables_count, scope_description)
run_ethics_reviewer(proposal_text)
```

Each function returns a structured dictionary that is collected by the orchestrator.

### 5.3 Tool Functions

File: `tools.py`

Important functions:

```python
search_literature(keywords)
check_existing_systems(domain)
check_timeline_realism(proposed_months, deliverables_count, scope_description)
check_team_scope_fit(team_size, scope_description)
```

These are pure simulated tools. They do not know about the agents or the orchestrator.

### 5.4 Sequential Orchestrator

File: `orchestrator.py`

Important functions:

```python
extract_proposal_sections(proposal)
detect_conflicts(specialist_reports)
synthesize_evaluation(proposal, specialist_reports, conflicts)
evaluate_proposal(proposal)
```

This file implements Part A of the lab.

### 5.5 Parallel Orchestrator

File: `orchestrator_async.py`

Important code:

```python
tech_report, novelty_report, feasibility_report, ethics_report = await asyncio.gather(
    run_agent_async(run_technical_reviewer, sections["technical"]),
    run_agent_async(run_novelty_assessor, sections["novelty_title"], sections["novelty_problem"]),
    run_agent_async(run_feasibility_analyst, ...),
    run_agent_async(run_ethics_reviewer, sections["ethics"]),
)
```

This file implements Part B of the lab.

## 6. Agent Isolation

Agent isolation is implemented in `extract_proposal_sections()` inside `orchestrator.py`.

The isolation design is:

| Specialist | Data Received |
| --- | --- |
| Technical Reviewer | Title, technical description, technology stack |
| Novelty Assessor | Title, problem statement |
| Feasibility Analyst | Proposed months, team size, deliverables count, scope |
| Ethics Reviewer | Problem statement, technical description |

This prevents agents from influencing each other. For example, the Novelty Assessor does not see the technical review, and the Feasibility Analyst does not see literature search results.

## 7. Graded Task 1: Ethics Reviewer

The fourth specialist is implemented in `agents.py`.

Function:

```python
run_ethics_reviewer(proposal_text)
```

It uses the Reflection pattern:

1. Generator creates an ethics assessment.
2. Critic reviews whether the assessment covers privacy, misuse, bias, Pakistan-specific considerations, and safeguards.
3. Generator revises if the critic does not approve.
4. The function returns the final ethics review with `risk_level`, `reflection_rounds`, and `critic_approved`.

The Ethics Reviewer checks:

- Data privacy concerns
- Potential misuse or harm
- Fairness and bias risks
- Pakistan-specific ethical considerations
- Responsible AI compliance

The orchestrator conflict detector includes this new conflict:

```text
Technical reviewer is positive, but Ethics Reviewer flags HIGH risk.
```

## 8. Graded Task 2: n8n Workflow

The n8n workflow file is:

```text
n8n_workflows/academic_paper_multiagent.json
```

Chosen domain: **Academic Paper Reviewer**

Specialists:

- Methodology Reviewer
- Contribution Reviewer

Workflow nodes:

| Node | Purpose |
| --- | --- |
| Webhook - Paper Submission | Accepts POST JSON body |
| Orchestrator - Select Specialists | Decides to call exactly two specialists |
| Tool - Methodology Quality Lookup | Simulated methodology tool using Code node |
| Tool - Contribution Gap Lookup | Simulated contribution/novelty tool using Code node |
| Agent - Methodology Reviewer | Groq HTTP node for methodology review |
| Agent - Contribution Reviewer | Groq HTTP node for contribution review |
| Merge - Specialist Reports | Combines both specialist outputs |
| Synthesis Agent - Final Review | Groq HTTP node that synthesizes the reports |
| Respond - Multi-Agent Review | Returns final JSON response to Postman |

## 9. Setup Instructions

Open PowerShell in the project folder:

```powershell
cd d:\multiagent-fyp-evaluator
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Create `.env` from `.env.example`:

```powershell
Copy-Item .env.example .env
```

Open `.env` and add your Groq key:

```text
GROQ_API_KEY=your_real_groq_key_here
GROQ_MODEL=llama-3.1-8b-instant
```

Important: Do not commit `.env`. It is already ignored by `.gitignore`.

## 10. Run the Server

Start FastAPI:

```powershell
uvicorn main:app --reload --port 8000
```

Expected output includes:

```text
Uvicorn running on http://127.0.0.1:8000
```

Open API docs in browser:

```text
http://127.0.0.1:8000/docs
```

## 11. Postman Test 1: Health Check

Method:

```text
GET
```

URL:

```text
http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "architecture": "Hub and Spoke - Orchestrator + 4 Specialists",
  "agents": {
    "orchestrator": "Coordination and synthesis only - no domain work",
    "technical_reviewer": "Reflection pattern (Lab 07)",
    "novelty_assessor": "Tool Use pattern (Lab 08)",
    "feasibility_analyst": "ReAct pattern (Lab 06)",
    "ethics_reviewer": "Reflection pattern for Responsible AI review"
  }
}
```

What to show in screenshot:

- `status: ok`
- Four specialist agents
- `ethics_reviewer` included

## 12. Postman Test 2: Strong Proposal Sequential Evaluation

Method:

```text
POST
```

URL:

```text
http://127.0.0.1:8000/evaluate
```

Headers:

```text
Content-Type: application/json
```

Body:

```json
{
  "title": "AI-Based Cloudburst Early Warning System for KPK",
  "problem_statement": "KPK faces devastating cloudburst events annually with no AI-based early warning system. PMD ground stations are absent in high-risk mountainous districts.",
  "technical_description": "ConvLSTM model trained on NASA GPM-IMERG satellite data and ERA5 atmospheric variables. FastAPI backend. React dashboard. Deployed on AWS.",
  "technology_stack": "Python, TensorFlow, FastAPI, React, PostgreSQL, AWS",
  "proposed_months": 10,
  "team_size": 3,
  "deliverables_count": 6
}
```

Expected fields in response:

```text
execution_mode: sequential
execution_time_s: number
specialist_reports.technical_reviewer
specialist_reports.novelty_assessor
specialist_reports.feasibility_analyst
specialist_reports.ethics_reviewer
conflicts_detected
final_evaluation
```

What to check:

- Technical reviewer has `reflection_rounds`
- Novelty assessor has `tools_called`
- Feasibility analyst has `reasoning_trace`
- Ethics reviewer has `risk_level`
- Final evaluation combines all specialist reports

## 13. Postman Test 3: Weak Proposal Sequential Evaluation

Method:

```text
POST
```

URL:

```text
http://127.0.0.1:8000/evaluate
```

Headers:

```text
Content-Type: application/json
```

Body:

```json
{
  "title": "A Chatbot for University Students",
  "problem_statement": "Students sometimes have questions about university procedures.",
  "technical_description": "We will make a chatbot using Python.",
  "technology_stack": "Python",
  "proposed_months": 3,
  "team_size": 2,
  "deliverables_count": 2
}
```

What to check:

- Final verdict should be weaker than the strong proposal.
- Novelty assessor should identify many existing chatbot-style systems.
- Technical reviewer should flag missing technical detail.
- Feasibility analyst should evaluate the short timeline and small scope.

## 14. Postman Test 4: Ethics-Risk Proposal

Method:

```text
POST
```

URL:

```text
http://127.0.0.1:8000/evaluate
```

Headers:

```text
Content-Type: application/json
```

Body:

```json
{
  "title": "AI Facial Recognition Attendance and Campus Monitoring System",
  "problem_statement": "Universities need automated attendance and behavior monitoring for students across campus gates and classrooms.",
  "technical_description": "The system uses facial recognition on CCTV streams, stores biometric templates, and flags suspicious student movement in real time through an admin dashboard.",
  "technology_stack": "Python, OpenCV, FaceNet, FastAPI, React, PostgreSQL",
  "proposed_months": 8,
  "team_size": 3,
  "deliverables_count": 5
}
```

What to check:

- `specialist_reports.ethics_reviewer.risk_level` should be `HIGH`
- Ethics review should discuss privacy, consent, surveillance, fairness, bias, and safeguards
- `conflicts_detected` should include `technical_ethics_conflict` if technical review is positive while ethics risk is high
- `final_evaluation` should include ethics as a major concern

## 15. Postman Test 5: Parallel Evaluation

Method:

```text
POST
```

URL:

```text
http://127.0.0.1:8000/evaluate/parallel
```

Headers:

```text
Content-Type: application/json
```

Use the same body as the strong proposal.

Expected fields:

```text
execution_mode: parallel
execution_time_s: number
specialist_reports
conflicts_detected
final_evaluation
```

Record:

```text
Sequential time = ______ seconds
Parallel time = ______ seconds
Speedup ratio = sequential_time / parallel_time
```

Expected explanation:

Parallel mode should normally be faster because all specialists start at the same time. If Groq rate limits occur, the speedup may be lower.

## 16. PowerShell Testing Commands

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Run strong proposal:

```powershell
$proposals = Get-Content .\test_proposals.json | ConvertFrom-Json
$body = $proposals.strong_proposal | ConvertTo-Json -Depth 20
Invoke-RestMethod http://127.0.0.1:8000/evaluate -Method Post -ContentType "application/json" -Body $body
```

Run parallel strong proposal:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/evaluate/parallel -Method Post -ContentType "application/json" -Body $body
```

Run ethics proposal:

```powershell
$ethics = $proposals.ethics_risk_proposal | ConvertTo-Json -Depth 20
Invoke-RestMethod http://127.0.0.1:8000/evaluate -Method Post -ContentType "application/json" -Body $ethics
```

## 17. n8n Import and Test Instructions

### 17.1 Import Workflow

1. Open n8n.
2. Click **Import from File**.
3. Select:

```text
n8n_workflows/academic_paper_multiagent.json
```

4. Save the workflow.

### 17.2 Add Groq Key to n8n

The workflow uses HTTP Request nodes and reads:

```text
{{$env.GROQ_API_KEY}}
```

Set `GROQ_API_KEY` in your n8n environment before running the workflow.

### 17.3 n8n Webhook Test Body

Send this JSON to the n8n webhook URL:

```json
{
  "title": "Improving Fake News Detection Using Transformer Models",
  "abstract": "This paper proposes a transformer-based approach for classifying fake news in online articles.",
  "methodology": "The study uses a labeled dataset of online news articles, preprocesses text, fine-tunes a transformer model, compares it with baseline machine learning classifiers, and reports precision, recall, F1-score, and confusion matrix results.",
  "research_gap": "Existing studies often evaluate fake news detection on generic datasets without enough focus on explainability and error analysis. This work aims to compare transformer performance with interpretable baselines and provide detailed misclassification analysis.",
  "keywords": ["fake news", "transformer", "classification", "explainability"],
  "sample_size": 5000,
  "study_design": "experimental comparative study"
}
```

Expected n8n response:

```json
{
  "specialist_1_output": "...",
  "specialist_2_output": "...",
  "synthesis": "...",
  "agent_names": ["Methodology Reviewer", "Contribution Reviewer"]
}
```

### 17.4 What to Explain During n8n Demo

Explain these points:

- The Webhook node receives the paper submission.
- The Orchestrator node selects exactly two specialists.
- Each specialist has an isolated role.
- Each specialist uses one Code node as a simulated tool.
- The Methodology Reviewer checks research design only.
- The Contribution Reviewer checks novelty and research gap only.
- The Synthesis Agent combines both reports.
- The Respond node returns both specialist outputs and the final synthesis.

## 18. Verification Performed

The following checks were run locally:

```powershell
python -m pip install -r requirements.txt
python -m compileall .
python -m json.tool n8n_workflows/academic_paper_multiagent.json
```

FastAPI endpoint checks were also run:

- `GET /health`
- `POST /evaluate` with strong proposal
- `POST /evaluate` with weak proposal
- `POST /evaluate` with ethics-risk proposal
- `POST /evaluate/parallel` with strong proposal

Live Groq verification was performed after adding the key to local ignored `.env`.

Direct Groq check:

```text
GROQ_DIRECT_CHECK=PASS
```

Endpoint verification summary:

| Test | Result |
| --- | --- |
| Health check | Passed, returned orchestrator and all four specialists |
| Strong proposal sequential | Passed, `execution_mode: sequential` |
| Weak proposal sequential | Passed, final verdict differed from strong proposal |
| Ethics-risk proposal | Passed, `risk_level: HIGH` |
| Ethics conflict | Passed, included `technical_ethics_conflict` |
| Parallel strong proposal | Passed, `execution_mode: parallel` |
| n8n JSON validation | Passed |

Timing values from the live run:

```text
Sequential /evaluate: 55.094 seconds
Parallel /evaluate/parallel: 61.125 seconds
Speedup ratio: 55.094 / 61.125 = 0.90
```

In this run, the parallel endpoint was not faster because Groq free-tier limits and the shared external LLM dependency became the bottleneck. This is still a useful production lesson: parallelism improves architecture, but external rate limits can reduce or remove speedup during live execution.

## 19. Important Notes About Groq Key

The Groq key must only be added to local `.env`.

Do not paste the real key into:

- `README.md`
- `LAB_REPORT.md`
- `SUBMISSION_NOTES.md`
- GitHub commits
- n8n exported JSON

The committed `.env.example` contains only:

```text
GROQ_API_KEY=your_groq_key_here
GROQ_MODEL=llama-3.1-8b-instant
```

## 20. Reflection Answer

Adding the Ethics Reviewer shows that the Hub-and-Spoke architecture separates specialist concerns from orchestration logic. The existing Technical, Novelty, and Feasibility agents did not need to be rewritten when the fourth specialist was added. Only the orchestrator wiring, conflict detection, and synthesis prompt needed updates. This proves that each specialist is isolated and independently replaceable. In a production system, such as a law firm document review pipeline, this is commercially important because new specialist reviewers can be added for privacy, compliance, jurisdiction, or risk without rebuilding the entire application. This reduces cost, improves maintainability, and allows the system to grow as customer requirements change.

## 21. Submission Checklist

Submit or show:

- GitHub repository link
- FastAPI `/health` screenshot
- Postman strong proposal response screenshot
- Postman weak proposal response screenshot
- Postman ethics-risk response screenshot
- Postman parallel response screenshot
- Sequential and parallel timing comparison
- n8n workflow canvas screenshot
- n8n exported workflow JSON
- n8n Postman response screenshot
- Reflection answer from this report or `SUBMISSION_NOTES.md`
