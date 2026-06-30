"""
Backoffice FastAPI console — trigger runs, browse dashboards, compare regressions.

Launch:
    uv run uvicorn backoffice.app:app --port 8090 --reload
"""

from __future__ import annotations

import json
import threading
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from swarm_qa.agents import reporter
from swarm_qa.models import RunReport
from swarm_qa.regression import compare_runs, load_run, render_regression_md

app = FastAPI(title="QA-Swarm Backoffice")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

RUNS_DIR = Path(__file__).resolve().parent.parent / "swarm_qa" / "runs"


def _list_runs() -> list[dict]:
    runs = []
    if not RUNS_DIR.exists():
        return runs
    for d in sorted(RUNS_DIR.iterdir(), reverse=True):
        run_json = d / "run.json"
        if run_json.exists():
            try:
                rpt = RunReport.model_validate_json(run_json.read_text(encoding="utf-8"))
                runs.append(
                    {
                        "run_id": rpt.run_id,
                        "version": rpt.sut_version,
                        "channels": ", ".join(rpt.channels),
                        "pass_rate": rpt.pass_rate,
                        "total": rpt.total,
                        "passed": rpt.passed,
                        "fix_plan_count": len(rpt.failure_analyses),
                        "created_at": rpt.created_at,
                        "has_html": (d / "report.html").exists(),
                        "has_fix_plan": (d / "fix_plan.json").exists()
                        and bool(rpt.failure_analyses),
                    }
                )
            except Exception:
                pass
    return runs


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"runs": _list_runs()})


@app.get("/runs/{run_id}/dashboard", response_class=HTMLResponse)
async def dashboard(run_id: str):
    html_path = RUNS_DIR / run_id / "report.html"
    if html_path.exists():
        return HTMLResponse(html_path.read_text(encoding="utf-8"))
    return HTMLResponse(
        "<p>Dashboard not found. Install the <code>report</code> extra.</p>", status_code=404
    )


@app.get("/runs/{run_id}/report", response_class=HTMLResponse)
async def report_md(request: Request, run_id: str):
    md_path = RUNS_DIR / run_id / "report.md"
    content = md_path.read_text(encoding="utf-8") if md_path.exists() else "Report not found."
    return templates.TemplateResponse(
        request=request, name="report.html", context={"run_id": run_id, "content": content}
    )


@app.get("/runs/{run_id}/json")
async def report_json(run_id: str):
    json_path = RUNS_DIR / run_id / "run.json"
    if json_path.exists():
        return json.loads(json_path.read_text(encoding="utf-8"))
    return {"error": "not found"}


@app.get("/runs/{run_id}/fix-plan", response_class=HTMLResponse)
async def fix_plan_md(request: Request, run_id: str):
    json_path = RUNS_DIR / run_id / "fix_plan.json"
    if not json_path.exists():
        content = "No fix plan found for this run."
    else:
        rpt = load_run(RUNS_DIR / run_id / "run.json")
        if not rpt.failure_analyses:
            content = "No failures were detected, so no fix plan was generated."
        else:
            lines = [f"# Fix Plan - {run_id}", ""]
            for analysis in rpt.failure_analyses:
                triage = analysis.triage
                plan = analysis.fix_plan
                lines += [
                    f"## {triage.failure_id}: {triage.intent} [{triage.channel}]",
                    "",
                    f"- Category: `{triage.category}`",
                    f"- Severity: `{triage.severity}`",
                    f"- Confidence: {triage.confidence:.0%}",
                    f"- Likely owner: {triage.likely_owner}",
                    f"- Auto-apply: `{plan.auto_apply}`",
                    "",
                    "### Hypothesis",
                    plan.root_cause_hypothesis,
                    "",
                    "### Affected files",
                ]
                lines.extend(f"- `{file}`" for file in plan.affected_files)
                lines += ["", "### Steps"]
                for idx, step in enumerate(plan.steps, 1):
                    lines.append(f"{idx}. **{step.title}** - {step.detail}")
                lines += ["", "### Verification"]
                lines.extend(f"- `{cmd}`" for cmd in plan.verification_commands)
                lines.append("")
            content = "\n".join(lines)
    return templates.TemplateResponse(
        request=request, name="report.html", context={"run_id": f"{run_id} fix plan", "content": content}
    )


@app.get("/runs/{run_id}/fix-plan/json")
async def fix_plan_json(run_id: str):
    json_path = RUNS_DIR / run_id / "fix_plan.json"
    if json_path.exists():
        return json.loads(json_path.read_text(encoding="utf-8"))
    return {"error": "not found"}


@app.get("/scenarios", response_class=HTMLResponse)
async def scenarios(request: Request):
    from swarm_qa.agents.generator import load_corpus

    cases = load_corpus()
    return templates.TemplateResponse(request=request, name="scenarios.html", context={"cases": cases})


@app.post("/trigger")
async def trigger_run(
    channels: str = Form("api"),
    version: str = Form("current"),
    limit: int = Form(0),
):
    ch_list = [c.strip() for c in channels.split(",") if c.strip()]

    def _run():
        from swarm_qa.pipeline import run_pipeline

        rpt = run_pipeline(channels=ch_list, limit=limit or None, sut_version=version)
        reporter.save_report(rpt)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return RedirectResponse("/", status_code=303)


@app.get("/regression", response_class=HTMLResponse)
async def regression_form(request: Request):
    runs = _list_runs()
    return templates.TemplateResponse(
        request=request, name="regression.html", context={"runs": runs, "result": None}
    )


@app.post("/regression", response_class=HTMLResponse)
async def regression_compare(
    request: Request,
    baseline: str = Form(...),
    candidate: str = Form(...),
):
    runs = _list_runs()
    try:
        base_rpt = load_run(RUNS_DIR / baseline / "run.json")
        cand_rpt = load_run(RUNS_DIR / candidate / "run.json")
        reg = compare_runs(base_rpt, cand_rpt)
        md = render_regression_md(reg)
    except Exception as e:
        md = f"Error comparing runs: {e}"
    return templates.TemplateResponse(
        request=request, name="regression.html", context={"runs": runs, "result": md}
    )
