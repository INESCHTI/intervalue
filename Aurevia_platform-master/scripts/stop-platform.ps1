param(
    [switch]$KeepDocker
)

$ErrorActionPreference = "SilentlyContinue"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Ports = @(5173, 8000, 8001, 8002, 8003, 8004, 8005, 8006)

foreach ($Port in $Ports) {
    $connections = Get-NetTCPConnection -LocalPort $Port
    foreach ($connection in $connections) {
        if ($connection.OwningProcess) {
            Stop-Process -Id $connection.OwningProcess -Force
        }
    }
}

if (-not $KeepDocker) {
    Set-Location $Root
    docker compose -f docker-compose.dev.yml down
}

Write-Host "Aurevia local services stopped."
