[CmdletBinding()]
param(
    [string]$OutDir = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($OutDir)) {
    $OutDir = Join-Path $repoRoot "results\clamp3_spike"
}
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

function Test-CommandAvailable {
    param([Parameter(Mandatory = $true)][string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Invoke-Captured {
    param(
        [Parameter(Mandatory = $true)][scriptblock]$Command
    )
    try {
        return (& $Command 2>&1 | Out-String).Trim()
    }
    catch {
        return "ERROR: $($_.Exception.Message)"
    }
}

$inventory = [ordered]@{
    schema_version = 1
    collected_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    repo_root = $repoRoot
    computer_name = $env:COMPUTERNAME
    os = [ordered]@{
        caption = ""
        version = ""
        build = ""
    }
    commands = [ordered]@{
        git = (Test-CommandAvailable "git")
        py = (Test-CommandAvailable "py")
        python = (Test-CommandAvailable "python")
        nvidia_smi = (Test-CommandAvailable "nvidia-smi")
        ffmpeg = (Test-CommandAvailable "ffmpeg")
    }
    python_launcher = [ordered]@{
        registered = ""
        py310_available = $false
        py311_available = $false
        py312_available = $false
        py313_available = $false
    }
    nvidia = [ordered]@{
        query = ""
    }
    core_runtime = $null
    notes = @()
}

try {
    $osInfo = Get-CimInstance Win32_OperatingSystem
    $inventory.os.caption = [string]$osInfo.Caption
    $inventory.os.version = [string]$osInfo.Version
    $inventory.os.build = [string]$osInfo.BuildNumber
}
catch {
    $inventory.notes += "Win32_OperatingSystem query failed: $($_.Exception.Message)"
}

if ($inventory.commands.py) {
    $inventory.python_launcher.registered = Invoke-Captured { py -0p }
    foreach ($version in @("3.10", "3.11", "3.12", "3.13")) {
        $available = $false
        try {
            & py "-$version" -c "import sys; print(sys.executable)" *> $null
            $available = ($LASTEXITCODE -eq 0)
        }
        catch {
            $available = $false
        }
        switch ($version) {
            "3.10" { $inventory.python_launcher.py310_available = $available }
            "3.11" { $inventory.python_launcher.py311_available = $available }
            "3.12" { $inventory.python_launcher.py312_available = $available }
            "3.13" { $inventory.python_launcher.py313_available = $available }
        }
    }
}
else {
    $inventory.notes += "Python launcher 'py' is not available."
}

if ($inventory.commands.nvidia_smi) {
    $inventory.nvidia.query = Invoke-Captured {
        nvidia-smi --query-gpu=name,driver_version,memory.total,compute_cap --format=csv,noheader
    }
}
else {
    $inventory.notes += "nvidia-smi is not available."
}

$corePython = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (Test-Path -LiteralPath $corePython -PathType Leaf) {
    $probeCode = @'
import json
import platform
import sys
try:
    import torch
    data = {
        "python": sys.version,
        "executable": sys.executable,
        "platform": platform.platform(),
        "torch": torch.__version__,
        "cuda_available": bool(torch.cuda.is_available()),
        "torch_cuda": torch.version.cuda,
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "capability": list(torch.cuda.get_device_capability(0)) if torch.cuda.is_available() else None,
        "compiled_arches": list(torch.cuda.get_arch_list()) if torch.cuda.is_available() else [],
    }
except Exception as exc:
    data = {"probe_error": f"{type(exc).__name__}: {exc}"}
print(json.dumps(data, ensure_ascii=False))
'@
    try {
        $json = & $corePython -c $probeCode
        if ($LASTEXITCODE -eq 0) {
            $inventory.core_runtime = $json | ConvertFrom-Json
        }
        else {
            $inventory.core_runtime = [ordered]@{ probe_error = "core Python probe exited $LASTEXITCODE" }
        }
    }
    catch {
        $inventory.core_runtime = [ordered]@{ probe_error = $_.Exception.Message }
    }
}
else {
    $inventory.notes += "Core .venv Python not found at $corePython"
}

$outPath = Join-Path $OutDir "clamp3_windows_inventory.json"
$inventory | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $outPath -Encoding utf8

Write-Host "CLaMP 3 Windows inventory completed."
Write-Host "Output: $outPath"
Write-Host "This probe did not install packages or download model weights."
