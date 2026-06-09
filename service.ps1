param(
    [Parameter(Mandatory = $true, ParameterSetName = "Action")]
    [ValidateSet("install", "start", "stop", "enable", "disable", "uninstall", "status")]
    [string]$Action,
    [Parameter(ParameterSetName = "Flags")][switch]$install,
    [Parameter(ParameterSetName = "Flags")][switch]$start,
    [Parameter(ParameterSetName = "Flags")][switch]$stop,
    [Parameter(ParameterSetName = "Flags")][switch]$enable,
    [Parameter(ParameterSetName = "Flags")][switch]$disable,
    [Parameter(ParameterSetName = "Flags")][switch]$uninstall,
    [Parameter(ParameterSetName = "Flags")][switch]$status,
    [string]$PythonExe = "",
    [string]$ServiceScript = "C:\\label-upload\\service.py"
)

$ErrorActionPreference = "Stop"
$ServiceName = "LabelUpload"

function Resolve-PythonExe {
    param([string]$Preferred)
    if ($Preferred) {
        if ((Split-Path -Leaf $Preferred) -ieq "py.exe") {
            return (& $Preferred -3.11 -c "import sys; print(sys.executable)").Trim()
        }
        return $Preferred
    }
    $launcher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($launcher) {
        return (& $launcher.Source -3.11 -c "import sys; print(sys.executable)").Trim()
    }
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }
    throw "Python executable not found. Pass -PythonExe with full path to python.exe."
}

if ($PSCmdlet.ParameterSetName -eq "Flags") {
    if ($install) { $Action = "install" }
    elseif ($start) { $Action = "start" }
    elseif ($stop) { $Action = "stop" }
    elseif ($enable) { $Action = "enable" }
    elseif ($disable) { $Action = "disable" }
    elseif ($uninstall) { $Action = "uninstall" }
    elseif ($status) { $Action = "status" }
}

function Get-LabelService {
    return Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
}

if ($Action -eq "install" -or $Action -eq "uninstall") {
    $PythonExe = Resolve-PythonExe -Preferred $PythonExe
    $ServiceScript = (Resolve-Path $ServiceScript).Path
    $ServiceDir = Split-Path -Parent $ServiceScript
    $ServiceFile = Split-Path -Leaf $ServiceScript
}

switch ($Action) {
    "install" {
        $PythonRoot = Split-Path -Parent $PythonExe
        if (Test-Path (Join-Path (Split-Path -Parent $PythonRoot) "pyvenv.cfg")) {
            throw "Windows service installation requires global Python. Pass -PythonExe py.exe."
        }
        $PostInstall = Join-Path (Split-Path -Parent $PythonExe) "pywin32_postinstall.py"
        if (Test-Path $PostInstall) {
            & $PythonExe $PostInstall -install -quiet
            if ($LASTEXITCODE -ne 0) {
                throw "pywin32 post-install failed with exit code $LASTEXITCODE"
            }
        }

        $Command = if (Get-LabelService) { "update" } else { "install" }
        Push-Location $ServiceDir
        try {
            & $PythonExe $ServiceFile --startup auto $Command
            if ($LASTEXITCODE -ne 0) {
                throw "service.py failed with exit code $LASTEXITCODE"
            }
        }
        finally {
            Pop-Location
        }
    }
    "start" {
        Start-Service -Name $ServiceName
        (Get-Service -Name $ServiceName).WaitForStatus("Running", "00:00:30")
        Get-Service -Name $ServiceName
    }
    "stop" {
        $Service = Get-LabelService
        if ($Service -and $Service.Status -ne "Stopped") {
            Stop-Service -Name $ServiceName
            $Service.WaitForStatus("Stopped", "00:00:30")
        }
        Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    }
    "enable" {
        Set-Service -Name $ServiceName -StartupType Automatic
        Get-Service -Name $ServiceName
    }
    "disable" {
        Set-Service -Name $ServiceName -StartupType Disabled
        Get-Service -Name $ServiceName
    }
    "uninstall" {
        $Service = Get-LabelService
        if (-not $Service) {
            Write-Host "Service is not installed."
            break
        }
        if ($Service.Status -ne "Stopped") {
            Stop-Service -Name $ServiceName
            $Service.WaitForStatus("Stopped", "00:00:30")
        }
        Push-Location $ServiceDir
        try {
            & $PythonExe $ServiceFile remove
            if ($LASTEXITCODE -ne 0) {
                throw "service.py failed with exit code $LASTEXITCODE"
            }
        }
        finally {
            Pop-Location
        }
    }
    "status" {
        $Service = Get-LabelService
        if ($Service) {
            $Service
        }
        else {
            Write-Host "Service is not installed."
        }
    }
}
