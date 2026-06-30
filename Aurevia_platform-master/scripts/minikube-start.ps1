param(
    [string]$Profile = "aurevia",
    [int]$Cpus = 4,
    [int]$MemoryMb = 6144,
    [switch]$SkipBuild,
    [switch]$NoPortForward
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Namespace = "wealthmesh"
$Release = "wealthmesh"
$Tag = "dev"
$Services = @(
    "orchestrator",
    "agent-financial",
    "agent-market",
    "agent-docs",
    "agent-action",
    "agent-qa",
    "voice"
)

function Resolve-Tool {
    param(
        [string]$Name,
        [string[]]$Candidates
    )

    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }

    foreach ($candidate in $Candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    throw "$Name is not installed or not available in PATH. Close and reopen PowerShell, or reinstall $Name."
}

function Start-PortForwardWindow {
    param(
        [string]$Title,
        [string]$ArgsLine
    )

    $script = @"
`$Host.UI.RawUI.WindowTitle = '$Title'
& '$KubectlExe' $ArgsLine
"@

    Start-Process powershell.exe -ArgumentList @(
        "-NoExit",
        "-ExecutionPolicy", "Bypass",
        "-Command", $script
    )
}

Set-Location $Root

$env:MINIKUBE_IN_STYLE = "false"

$MinikubeExe = Resolve-Tool "minikube" @(
    "C:\Program Files\Kubernetes\Minikube\minikube.exe",
    "$env:LOCALAPPDATA\Microsoft\WinGet\Links\minikube.exe"
)
$KubectlExe = Resolve-Tool "kubectl" @(
    "$env:LOCALAPPDATA\Microsoft\WinGet\Links\kubectl.exe"
)
$HelmExe = Resolve-Tool "helm" @(
    "$env:LOCALAPPDATA\Microsoft\WinGet\Links\helm.exe"
)

Write-Host "Starting Minikube profile '$Profile'..."
& $MinikubeExe start `
    --profile $Profile `
    --cpus $Cpus `
    --memory "$($MemoryMb)mb" `
    --driver docker `
    --kubernetes-version v1.30.0 `
    --addons ingress,metrics-server

Write-Host "Selecting Minikube profile..."
& $MinikubeExe profile $Profile

if (-not $SkipBuild) {
    Write-Host "Pointing Docker CLI to Minikube internal Docker daemon..."
    & $MinikubeExe -p $Profile docker-env --shell powershell | Invoke-Expression

    foreach ($Service in $Services) {
        Write-Host "Building wealthmesh/${Service}:${Tag} inside Minikube..."
        docker build `
            -f "services/$Service/Dockerfile" `
            -t "wealthmesh/${Service}:${Tag}" `
            --build-arg BUILDKIT_INLINE_CACHE=1 `
            .
    }

    Write-Host "Building wealthmesh/frontend:$Tag inside Minikube..."
    docker build `
        -f "frontend/Dockerfile" `
        -t "wealthmesh/frontend:$Tag" `
        --build-arg VITE_DEV_AUTH=true `
        --build-arg VITE_API_URL= `
        --build-arg VITE_KEYCLOAK_URL=/auth `
        .
}

Write-Host "Deploying Aurevia with Helm..."
& $HelmExe upgrade --install $Release helm/wealthmesh `
    --namespace $Namespace `
    --create-namespace `
    --set global.imagePullPolicy=Never `
    --set images.orchestrator.tag=$Tag `
    --set images.agentFinancial.tag=$Tag `
    --set images.agentMarket.tag=$Tag `
    --set images.agentDocs.tag=$Tag `
    --set images.agentAction.tag=$Tag `
    --set images.agentQa.tag=$Tag `
    --set images.voice.tag=$Tag `
    --set images.frontend.tag=$Tag `
    --set keycloak.url="" `
    --wait `
    --timeout 10m

& $KubectlExe -n $Namespace get pods

if (-not $NoPortForward) {
    Write-Host "Opening port-forward windows..."
    Start-PortForwardWindow "Aurevia frontend :5173" "-n $Namespace port-forward svc/frontend 5173:80"
    Start-PortForwardWindow "Aurevia API :8000" "-n $Namespace port-forward svc/orchestrator 8000:8000"
    Start-PortForwardWindow "Aurevia Keycloak :8180" "-n $Namespace port-forward svc/keycloak 8180:8080"
}

Write-Host ""
Write-Host "Aurevia on Minikube is starting."
Write-Host "Frontend: http://127.0.0.1:5173"
Write-Host "API:      http://127.0.0.1:8000"
Write-Host "Keycloak: http://127.0.0.1:8180"
Write-Host ""
Write-Host "Useful checks:"
Write-Host "  kubectl -n $Namespace get pods"
Write-Host "  kubectl -n $Namespace logs deploy/orchestrator"
Write-Host ""
Write-Host "Stop with:"
Write-Host "  powershell -ExecutionPolicy Bypass -File scripts\minikube-stop.ps1"
