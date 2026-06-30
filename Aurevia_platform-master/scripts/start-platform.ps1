param(
    [switch]$NoDocker,
    [switch]$NoAgents,
    [switch]$NoFrontend,
    [switch]$FullInfra
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")

function Start-AureviaWindow {
    param(
        [string]$Title,
        [string]$Command
    )

    $script = @"
`$Host.UI.RawUI.WindowTitle = '$Title'
Set-Location '$Root'
$Command
"@

    Start-Process powershell.exe -ArgumentList @(
        "-NoExit",
        "-ExecutionPolicy", "Bypass",
        "-Command", $script
    )
}

Set-Location $Root

if (-not $NoDocker) {
    Write-Host "Starting Docker infrastructure..."
    if ($FullInfra) {
        docker compose -f docker-compose.dev.yml up -d
    } else {
        docker compose -f docker-compose.dev.yml up -d postgres redis qdrant mailhog
    }
}

if (-not $NoAgents) {
    Start-AureviaWindow "Aurevia orchestrator :8000" "uv run python -m uvicorn orchestrator.main:app --host 127.0.0.1 --port 8000"
    Start-AureviaWindow "Aurevia financial agent :8001" "uv run python -m uvicorn agent_financial.main:app --host 127.0.0.1 --port 8001"
    Start-AureviaWindow "Aurevia market agent :8002" "uv run python -m uvicorn agent_market.main:app --host 127.0.0.1 --port 8002"
    Start-AureviaWindow "Aurevia docs agent :8003" "`$env:QDRANT_URL='http://127.0.0.1:6333'; uv run python -m uvicorn agent_docs.main:app --host 127.0.0.1 --port 8003"
    Start-AureviaWindow "Aurevia action agent :8004" "uv run python -m uvicorn agent_action.main:app --host 127.0.0.1 --port 8004"
    Start-AureviaWindow "Aurevia QA agent :8005" "uv run python -m uvicorn agent_qa.main:app --host 127.0.0.1 --port 8005"
    Start-AureviaWindow "Aurevia voice service :8006" "uv run python -m uvicorn voice.main:app --host 127.0.0.1 --port 8006"
}

if (-not $NoFrontend) {
    Start-AureviaWindow "Aurevia frontend :5173" "Set-Location '$Root\frontend'; `$env:VITE_DEV_AUTH='true'; npm.cmd run dev -- --host 127.0.0.1"
}

Write-Host ""
Write-Host "Aurevia is starting."
Write-Host "Frontend:     http://127.0.0.1:5173"
Write-Host "Backend API:  http://127.0.0.1:8000"
Write-Host "Keycloak:     http://127.0.0.1:8180"
Write-Host "Qdrant:       http://127.0.0.1:6333"
Write-Host ""
Write-Host "Close the opened PowerShell windows to stop app services."
Write-Host "Run scripts\stop-platform.ps1 to stop Docker infrastructure and kill service ports."
Write-Host "Use -FullInfra if you also want Traefik, Keycloak, Langfuse, and MLflow."
