# QA-Swarm — Complete Testing Guide (A to Z)

Run every test scenario manually, step by step. Each section is independent — run them in order or pick what you need.

---

## 0. Prerequisites — Start Everything

Open **separate terminals** for each service and keep them running:

```bash
# Terminal 1 — Ollama
ollama serve

# Terminal 2 — Orchestrator
cd C:\Users\amine\Desktop\project
uv run uvicorn orchestrator.main:app --port 8000

# Terminal 3 — Financial agent
cd C:\Users\amine\Desktop\project
uv run uvicorn agent_financial.main:app --port 8001

# Terminal 4 — Market agent
cd C:\Users\amine\Desktop\project
uv run uvicorn agent_market.main:app --port 8002

# Terminal 5 — Docs agent
cd C:\Users\amine\Desktop\project
uv run uvicorn agent_docs.main:app --port 8003

# Terminal 6 — Action agent
cd C:\Users\amine\Desktop\project
uv run uvicorn agent_action.main:app --port 8004

# Terminal 7 — QA agent
cd C:\Users\amine\Desktop\project
uv run uvicorn agent_qa.main:app --port 8005

# Terminal 8 — Frontend dev server
cd C:\Users\amine\Desktop\project\frontend
npx vite --port 5173

# Terminal 9 — This is your test terminal (run all commands below here)
cd C:\Users\amine\Desktop\project
```

**Or start everything at once (PowerShell one-liner):**

```powershell
cd C:\Users\amine\Desktop\project
Start-Process uv -ArgumentList "run","uvicorn","orchestrator.main:app","--port","8000"
Start-Process uv -ArgumentList "run","uvicorn","agent_financial.main:app","--port","8001"
Start-Process uv -ArgumentList "run","uvicorn","agent_market.main:app","--port","8002"
Start-Process uv -ArgumentList "run","uvicorn","agent_docs.main:app","--port","8003"
Start-Process uv -ArgumentList "run","uvicorn","agent_action.main:app","--port","8004"
Start-Process uv -ArgumentList "run","uvicorn","agent_qa.main:app","--port","8005"
cd frontend; Start-Process npx -ArgumentList "vite","--port","5173"
```

Verify everything is up:

```bash
curl http://localhost:11434/api/tags          # Ollama — should list models
curl http://localhost:8000/health             # Orchestrator — {"status":"ok"}
curl http://localhost:8001/health             # Financial agent — {"status":"ok"}
curl http://localhost:8002/health             # Market agent — {"status":"ok"}
curl http://localhost:8003/health             # Docs agent — {"status":"ok"}
curl http://localhost:8004/health             # Action agent — {"status":"ok"}
curl http://localhost:8005/health             # QA agent — {"status":"ok"}
curl http://localhost:5173                    # Frontend — HTML page
```

**IMPORTANT:** If the agent services (8001-8005) are not running, most tests will FAIL because the orchestrator can't route queries to the specialist agents. You'll see "couldn't retrieve info" responses and ~25% pass rate instead of ~90%+.

Make sure `qwen2.5:3b` is pulled:

```bash
ollama pull qwen2.5:3b
```

Install test dependencies (once):

```bash
uv pip install -e "qa-swarm[web,report,backoffice]"
uv run playwright install chromium
```

---

## 1. Unit Tests (no Ollama needed)

Run the full pytest suite — tests the pipeline, evaluator, regression detection, JSON extraction:

```bash
uv run pytest qa-swarm/tests/ -v
```

Expected: **16 passed**.

---

## 2. API Channel — Full 52 Scenarios

Tests the agent via `POST /api/chat` (SSE streaming). No browser needed.

```bash
# Full corpus (52 scenarios, ~20 min)
uv run python -u -m swarm_qa.pipeline --channel api --version v1.0

# Quick smoke (5 scenarios, ~2 min)
uv run python -u -m swarm_qa.pipeline --channel api --limit 5 --version smoke

# Only adversarial scenarios (test prompt injection, XSS, jailbreak etc.)
uv run python -u -m swarm_qa.pipeline --channel api --limit 52 --version adversarial
```

Each line shows: `[channel] intent  PASS/FAIL  score  latency  reason`

Reports saved to `qa-swarm/swarm_qa/runs/<run_id>/`:
- `run.json` — raw results
- `report.md` — Markdown table
- `report.html` — open in browser for interactive Plotly dashboard

---

## 3. Web Channel — Playwright Browser Testing (with visible Chromium)

Launches a real Chromium browser, navigates to the chat page, types the question, waits for the streaming response, takes a screenshot.

```bash
# Visible browser (you watch Chromium open and type)
uv run python -u -m swarm_qa.pipeline --channel web --limit 5 --version web-test

# Headless (faster, no visible browser)
QA_HEADLESS=true uv run python -u -m swarm_qa.pipeline --channel web --limit 5 --version web-headless
```

Screenshots saved in: `qa-swarm/swarm_qa/runs/_screens/S*_web_*.png`

**Multi-channel (API + Web simultaneously):**

```bash
uv run python -u -m swarm_qa.pipeline --channel api web --limit 5 --version multi
```

---

## 4. Mobile Channel — Appium (Android Emulator)

Requires extra setup. Skip if you don't have an Android emulator.

### Setup (once)

```bash
npm install -g appium
appium driver install uiautomator2
```

Start Android Studio, launch an AVD (emulator), then install/start the Expo app on it.

```bash
# Terminal — start Appium server
appium

# In another terminal — start the Expo app
cd C:\Users\amine\Desktop\project\mobile
npx expo start --android
```

### Run

```bash
uv run python -u -m swarm_qa.pipeline --channel mobile --limit 3 --version mobile-test
```

### All 3 channels at once (API + Web + Mobile)

```bash
uv run python -u -m swarm_qa.pipeline --channel api web mobile --limit 3 --version all-channels
```

This also computes **Web↔Mobile divergence** — if the web and mobile replies differ by >20%, it flags a FAIL.

---

## 5. Regression Detection — Compare Two Runs

The success criterion from the project brief: detect when a new version breaks things.

### Step 1: Create a baseline run

```bash
uv run python -u -m swarm_qa.pipeline --channel api --limit 10 --version baseline
```

Note the run_id printed at the end (e.g., `run_20260618_155812_a21aab`).

### Step 2: Change something in the agent (or just run again)

```bash
uv run python -u -m swarm_qa.pipeline --channel api --limit 10 --version candidate
```

### Step 3: Compare

```python
uv run python -c "
from pathlib import Path
from swarm_qa.regression import compare_from_files, render_regression_md

# Replace with your actual run_ids
baseline = Path('qa-swarm/swarm_qa/runs/YOUR_BASELINE_RUN_ID/run.json')
candidate = Path('qa-swarm/swarm_qa/runs/YOUR_CANDIDATE_RUN_ID/run.json')

reg = compare_from_files(baseline, candidate)
print(render_regression_md(reg))
print(f'Flips: {len(reg.flips)}, Score drops: {len(reg.score_drops)}, Latency spikes: {len(reg.latency_spikes)}')
"
```

Or use the backoffice UI (section 7).

---

## 6. CI Smoke Gate

Quick 5-scenario check that exits 0 (pass) or 1 (fail). Use in CI/pre-merge:

```bash
uv run python qa-swarm/ci_smoke.py
```

---

## 7. Backoffice Console (Web UI)

A browser-based dashboard to trigger runs, view results, and compare regressions.

```bash
uv pip install -e "qa-swarm[backoffice]"
uv run uvicorn backoffice.app:app --port 8090 --reload
```

Open **http://localhost:8090** in your browser:

- **Home page** → see all past runs, trigger a new run (choose channels, version, limit)
- **Scenarios** → browse all 52 test cases (nominal / limit / adversarial)
- **Regression** → pick two runs and compare for PASS→FAIL flips
- **Dashboard** → click "Dashboard" on any run to open the interactive Plotly charts

---

## 8. View Plotly Dashboards Directly

Every run generates an HTML dashboard. Open it in your browser:

```bash
# List all runs
ls qa-swarm/swarm_qa/runs/

# Open a dashboard (replace with your run_id)
start qa-swarm/swarm_qa/runs/run_20260618_155812_a21aab/report.html
```

The dashboard shows: pass rate by type, latency by channel, score distribution, failure breakdown.

---

## 9. Full A-to-Z Demo Run (everything at once)

```bash
# 1. Unit tests
uv run pytest qa-swarm/tests/ -v

# 2. Baseline run — API + Web, 10 scenarios, visible browser
uv run python -u -m swarm_qa.pipeline --channel api web --limit 10 --version v1-baseline

# 3. Open the dashboard
start qa-swarm/swarm_qa/runs/run_*/report.html

# 4. Second run (simulate new version)
uv run python -u -m swarm_qa.pipeline --channel api web --limit 10 --version v2-candidate

# 5. Start backoffice and compare regressions in the browser
uv run uvicorn backoffice.app:app --port 8090 --reload
# → open http://localhost:8090/regression, select baseline vs candidate, click Compare

# 6. CI smoke gate
uv run python qa-swarm/ci_smoke.py
```

---

## Command Reference

| What | Command |
|---|---|
| Unit tests | `uv run pytest qa-swarm/tests/ -v` |
| API only (quick) | `uv run python -u -m swarm_qa.pipeline --channel api --limit 5` |
| API only (full) | `uv run python -u -m swarm_qa.pipeline --channel api --version v1` |
| Web visible | `uv run python -u -m swarm_qa.pipeline --channel web --limit 5` |
| Web headless | `QA_HEADLESS=true uv run python -u -m swarm_qa.pipeline --channel web --limit 5` |
| API + Web | `uv run python -u -m swarm_qa.pipeline --channel api web --limit 10` |
| All 3 channels | `uv run python -u -m swarm_qa.pipeline --channel api web mobile --limit 3` |
| Mobile only | `uv run python -u -m swarm_qa.pipeline --channel mobile --limit 3` |
| CI smoke | `uv run python qa-swarm/ci_smoke.py` |
| Backoffice UI | `uv run uvicorn backoffice.app:app --port 8090 --reload` |
| Open dashboard | `start qa-swarm/swarm_qa/runs/<run_id>/report.html` |

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `QA_HEADLESS` | `false` | Set to `true` for headless Playwright |
| `SUT_API_URL` | `http://localhost:8000` | Orchestrator URL |
| `SUT_WEB_URL` | `http://localhost:5173` | Frontend URL |
| `SUT_DEV_TOKEN` | `dev-token` | Bearer token for API channel |
| `MODEL_GENERATOR` | `qwen2.5:3b` | Ollama model for Generator agent |
| `MODEL_EXECUTOR` | `qwen2.5:3b` | Ollama model for Executor agent |
| `MODEL_EVALUATOR` | `qwen2.5:3b` | Ollama model for Evaluator agent |
| `QA_TIMEOUT_SECONDS` | `30` | Max seconds per scenario |
| `QA_MIN_SCORE_PASS` | `3.0` | Minimum mean score to PASS |
| `APPIUM_URL` | `http://localhost:4723` | Appium server for mobile |
| `ANDROID_DEVICE` | `emulator-5554` | Android AVD device name |

## Troubleshooting

| Problem | Fix |
|---|---|
| `No module named 'playwright'` | `uv pip install -e "qa-swarm[web]"` then `uv run playwright install chromium` |
| `No module named 'plotly'` | `uv pip install -e "qa-swarm[report]"` |
| Web channel: "waiting for composer-input" timeout | Frontend not running or auth blocking. Set `VITE_DEV_AUTH=true` in `frontend/.env.development` and restart Vite |
| API channel: connection refused | Start the orchestrator: `uv run uvicorn services.orchestrator.src.orchestrator.main:app --port 8000` |
| Evaluator takes forever | Ollama not running or model not pulled. Run `ollama serve` and `ollama pull qwen2.5:3b` |
| Mobile: "Appium server unavailable" | Install and start Appium: `npm install -g appium && appium` |
| No output / buffered output | Always use `python -u` flag (already in the commands above) |
