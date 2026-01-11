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
    [string]$ServiceScript = "C:\\label-upload\\service.py",
    [string]$AppPath = "",
    [int]$Port = 8088
)

$ErrorActionPreference = "Stop"

function Resolve-PythonExe {
    param([string]$Preferred)
    if ($Preferred) {
        return $Preferred
    }
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }
    throw "Python executable not found. Pass -PythonExe with full path to python.exe."
}

$PythonExe = Resolve-PythonExe -Preferred $PythonExe
if (-not (Test-Path $ServiceScript)) {
    throw "ServiceScript not found: $ServiceScript"
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

$scriptArgs = @($ServiceScript, $Action)
if ($Action -eq "install") {
    if ($AppPath) {
        $scriptArgs += @("--app-path", $AppPath)
    }
    if ($Port) {
        $scriptArgs += @("--port", $Port)
    }
}

& $PythonExe @scriptArgs | Out-Host
if ($LASTEXITCODE -ne 0) {
    throw "service.py failed with exit code $LASTEXITCODE"
}
