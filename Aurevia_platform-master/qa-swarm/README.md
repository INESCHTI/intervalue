# Aurevia QA Swarm

This package implements the autonomous testing idea from `Value___Projet_SLMs.pdf`
around the Aurevia platform.

It follows the same Swarm-style responsibilities:

- `Generator Agent`: creates API/Web/Mobile scenarios.
- `Executor Agent`: runs scenarios against Aurevia.
- `Evaluator Agent`: scores actual results against expected evidence.
- `Reporter Agent`: writes Markdown, JSON, and CSV reports.

The implementation is intentionally runnable without a cloud API. It is
Swarm-style orchestration in local Python, and can later be replaced by the
OpenAI Swarm framework if needed.

## What Each Tool Does

### Minikube

Minikube runs a local Kubernetes cluster on your machine. In this project it is
used to test the same Aurevia services as if they were deployed in a production
cluster.

Use it when you want to validate:

- Kubernetes manifests / Helm chart
- service routing through `wealthmesh.local`
- behavior of the platform outside simple local `uvicorn` mode

### Playwright

Playwright opens a real browser and controls it like a user. In this package it
opens the Aurevia web app, goes to pages like `/chat` or `/`, types in inputs,
clicks buttons, waits for replies, and takes screenshots.

This replaces Selenium because the project brief recommends a code-based
Playwright approach for browser testing.

### DOM

The DOM is the HTML structure of the web page. Playwright uses DOM selectors such
as `input.composer-input` or `button[aria-label='Send message']` to find the
exact UI elements it needs to interact with.

This is more precise than only looking at screenshots.

### OCR

OCR reads text from screenshots. It is useful as visual evidence: even if the
DOM changes, the screenshot can still prove what the user actually saw.

This package uses `pytesseract` when Tesseract is installed.

## Install

From the repository root:

```powershell
cd D:\4DS\value\Aurevia_platform-master
uv sync --all-packages
```

For OCR, install the external Tesseract binary too. On Windows, install
Tesseract and make sure `tesseract.exe` is in `PATH`.

## Run Against Local Aurevia

Terminal 1:

```powershell
cd D:\4DS\value\Aurevia_platform-master
uv run uvicorn orchestrator.main:app --host 127.0.0.1 --port 8000
```

Terminal 2:

```powershell
cd D:\4DS\value\Aurevia_platform-master\frontend
$env:VITE_DEV_AUTH="true"
npm.cmd run dev -- --host 127.0.0.1
```

Terminal 3:

```powershell
cd D:\4DS\value\Aurevia_platform-master
uv run aurevia-qa-swarm
```

Run only API tests:

```powershell
uv run aurevia-qa-swarm --channel api
```

Run only Playwright Web/DOM/OCR tests:

```powershell
uv run aurevia-qa-swarm --channel web
```

## Run Against Minikube

After deploying Aurevia to Minikube and making `wealthmesh.local` reachable:

```powershell
cd D:\4DS\value\Aurevia_platform-master
$env:AUREVIA_TARGET="minikube"
uv run aurevia-qa-swarm
```

Override URLs manually if needed:

```powershell
$env:AUREVIA_API_URL="http://wealthmesh.local"
$env:AUREVIA_WEB_URL="http://wealthmesh.local"
uv run aurevia-qa-swarm
```

## Outputs

Reports are written to:

```text
reports/qa-swarm/report.md
reports/qa-swarm/results.json
reports/qa-swarm/results.csv
reports/qa-swarm/screenshots/
```

