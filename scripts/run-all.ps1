# =====================================================================
# run-all.ps1 — Launch the full LaRuche stack + QA-Swarm backoffice
#   - Docker infra (Postgres, Redis, Qdrant, Keycloak, MailHog, ...)
#   - 7 backend services (orchestrator + agents + voice) in dev-bypass
#   - Frontend (Vite dev server)
#   - QA-Swarm backoffice (FastAPI test UI)
# =====================================================================

$ErrorActionPreference = "Continue"
$Root = "C:\Users\amine\Desktop\project"
$Venv = "$Root\.venv\Scripts"
$Uvicorn = "$Venv\uvicorn.exe"

function Start-Svc($name, $appModule, $port, $srcDir, $extraEnv) {
  $existing = Test-NetConnection -ComputerName localhost -Port $port -WarningAction SilentlyContinue -InformationLevel Quiet
  if ($existing) { Write-Host "[$name] already up on $port" -ForegroundColor Yellow; return }
  $envPrefix = ""
  if ($extraEnv) { foreach ($kv in $extraEnv.GetEnumerator()) { Set-Item -Path "Env:$($kv.Key)" -Value $kv.Value } }
  Start-Process -FilePath $Uvicorn `
    -ArgumentList "$appModule`:app","--host","0.0.0.0","--port","$port" `
    -WorkingDirectory $srcDir -WindowStyle Hidden
  Write-Host "[$name] starting on $port" -ForegroundColor Green
}

# Common env for the mesh — dev-bypass auth, local Ollama, host Qdrant
$env:OLLAMA_BASE_URL = "http://localhost:11434"
$env:QDRANT_URL      = "http://localhost:6333"
Remove-Item Env:KEYCLOAK_URL -ErrorAction SilentlyContinue

Write-Host "`n=== 1. Backend mesh (7 services) ===" -ForegroundColor Cyan
Start-Svc "orchestrator" "orchestrator.main"      8000 "$Root\services\orchestrator\src"
Start-Svc "financial"    "agent_financial.main"   8001 "$Root\services\agent-financial\src"
Start-Svc "market"       "agent_market.main"      8002 "$Root\services\agent-market\src"
Start-Svc "docs"         "agent_docs.main"        8003 "$Root\services\agent-docs\src"
Start-Svc "action"       "agent_action.main"      8004 "$Root\services\agent-action\src"
Start-Svc "qa-agent"     "agent_qa.main"          8005 "$Root\services\agent-qa\src"
Start-Svc "voice"        "voice.main"             8006 "$Root\services\voice\src"

Write-Host "`n=== 2. QA-Swarm backoffice (test UI) ===" -ForegroundColor Cyan
$qaUp = Test-NetConnection -ComputerName localhost -Port 8090 -WarningAction SilentlyContinue -InformationLevel Quiet
if ($qaUp) { Write-Host "[qa-backoffice] already up on 8090" -ForegroundColor Yellow }
else {
  Start-Process -FilePath $Uvicorn `
    -ArgumentList "backoffice.app:app","--host","0.0.0.0","--port","8090" `
    -WorkingDirectory "$Root\qa-swarm" -WindowStyle Hidden
  Write-Host "[qa-backoffice] starting on 8090" -ForegroundColor Green
}

Write-Host "`nAll launch commands issued." -ForegroundColor Cyan
