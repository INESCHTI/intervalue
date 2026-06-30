param(
    [string]$Profile = "aurevia",
    [switch]$Delete
)

$ErrorActionPreference = "SilentlyContinue"
$Namespace = "wealthmesh"
$Ports = @(5173, 8000, 8180)

$env:MINIKUBE_IN_STYLE = "false"

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

    return $Name
}

$MinikubeExe = Resolve-Tool "minikube" @(
    "C:\Program Files\Kubernetes\Minikube\minikube.exe",
    "$env:LOCALAPPDATA\Microsoft\WinGet\Links\minikube.exe"
)
$KubectlExe = Resolve-Tool "kubectl" @(
    "$env:LOCALAPPDATA\Microsoft\WinGet\Links\kubectl.exe"
)

foreach ($Port in $Ports) {
    $connections = Get-NetTCPConnection -LocalPort $Port
    foreach ($connection in $connections) {
        if ($connection.OwningProcess) {
            Stop-Process -Id $connection.OwningProcess -Force
        }
    }
}

if ($Delete) {
    & $MinikubeExe delete --profile $Profile
} else {
    & $KubectlExe -n $Namespace delete pods --all
    & $MinikubeExe stop --profile $Profile
}

Write-Host "Aurevia Minikube environment stopped."
