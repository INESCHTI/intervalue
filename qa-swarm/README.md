# QA-Swarm - Autonomous Testing System

QA-Swarm is an autonomous testing pipeline for the LaRuche conversational agent. It runs
scenarios across API, Web, and Mobile channels, scores the answers, detects regressions, and
now produces safe manual fix plans for failed scenarios.

## Architecture

```text
Generator -> Executor -> Evaluator -> Reporter -> FixPlanner
                 |             |             |             |
               API/Web/Mobile  scoring       reports       plan only
```

The pipeline runs a versioned scenario corpus, captures raw channel results, scores each
result, writes reports, and generates a non-destructive triage/fix plan for failures.

| Agent | Role | Model |
|---|---|---|
| Generator | Loads or synthesizes test cases from the JSON corpus | qwen2.5:3b |
| Executor | Dispatches each case to API, Web, or Mobile | qwen2.5:3b |
| Evaluator | Scores pertinence, exactitude, coherence, and hallucination | qwen2.5:3b |
| Reporter | Produces Markdown and Plotly HTML reports | qwen2.5:3b |
| FixPlanner | Classifies failures and writes safe manual fix plans | deterministic heuristics / qwen2.5:3b agent card |

## Setup

Prerequisites:

- Python 3.12+
- `uv`
- Ollama running locally with `qwen2.5:3b`
- The LaRuche SUT running locally

Install:

```bash
cd qa-swarm
uv sync
uv pip install -e ".[web]"         # optional Playwright channel
uv pip install -e ".[mobile]"      # optional Appium channel
uv pip install -e ".[report]"      # optional Plotly dashboard
uv pip install -e ".[backoffice]"  # optional FastAPI console
```

Pull the default local model:

```bash
ollama pull qwen2.5:3b
```

## Usage

Run the API channel:

```bash
uv run python -m swarm_qa.pipeline --channel api
```

Run multiple channels:

```bash
uv run python -m swarm_qa.pipeline --channel api web --limit 5 --version baseline
```

Reports are saved to `swarm_qa/runs/<run_id>/`:

- `run.json`: full structured run output.
- `report.md`: Markdown report.
- `report.html`: Plotly dashboard when the report extra is installed.
- `fix_plan.json`: machine-readable triage and manual fix plans.

## Safe FixPlanner

FixPlanner is intentionally non-destructive. It only explains how to fix a failure.

For each failed scenario it produces:

- failure category
- severity
- confidence
- likely owner
- evidence
- likely files
- manual repair steps
- verification commands

Safety guarantees:

- It does not modify source files.
- It does not apply patches.
- It does not commit or push.
- Plans always use `auto_apply=false`.
- Plans always use `human_approval_required=true`.

Inspect a generated plan:

```bash
cat swarm_qa/runs/<run_id>/fix_plan.json
```

## Backoffice

Start the backoffice:

```bash
uv pip install -e ".[backoffice]"
uv run uvicorn backoffice.app:app --port 8090 --reload
```

Open `http://localhost:8090` to:

- trigger pipeline runs
- browse scenarios
- view dashboards
- compare regressions
- open the Fix plan page for failed runs

## Regression Detection

Compare two run JSON files:

```python
from pathlib import Path
from swarm_qa.regression import compare_from_files

reg = compare_from_files(
    Path("swarm_qa/runs/run_baseline/run.json"),
    Path("swarm_qa/runs/run_candidate/run.json"),
)

print(reg.has_regressions)
```

Regression checks include:

- PASS to FAIL flips
- score drops
- latency spikes

## Scoring

The evaluator scores:

- Pertinence: relevance to the user's intent
- Exactitude: factual correctness against the expected answer
- Coherence: logical consistency
- Hallucination: invented unsupported facts

Blocking failure rules:

- timeout
- crash or 5xx
- empty reply
- hallucination

## Test Corpus

The corpus lives in `swarm_qa/corpus/scenarios.json` and covers:

- nominal financial questions
- edge cases
- adversarial prompts
- API/Web/Mobile channel coverage

## Tests

```bash
uv run pytest tests -q
```

CI smoke:

```bash
uv run python ci_smoke.py
```

## Project Structure

```text
qa-swarm/
  swarm_qa/
    config.py
    client.py
    models.py
    pipeline.py
    regression.py
    extract.py
    agents/
      generator.py
      executor.py
      evaluator.py
      reporter.py
      fix_planner.py
    channels/
      api_channel.py
      web_channel.py
      mobile_channel.py
    corpus/
      scenarios.json
    scoring/
      metrics.py
    runs/
  backoffice/
    app.py
    templates/
  tests/
  ci_smoke.py
  pyproject.toml
```
