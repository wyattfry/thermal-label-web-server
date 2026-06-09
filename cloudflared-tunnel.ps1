[CmdletBinding()]
param(
    [ValidateSet("Install", "Start", "Stop", "Restart", "Status", "Uninstall")]
    [string]$Action = "Install"
)

$ErrorActionPreference = "Stop"

$TunnelName = "label-upload-print"
$Hostname = "print.wyattfry.com"
$Origin = "http://127.0.0.1:8088"
$ServiceName = "cloudflared-label-upload"
$DataDir = Join-Path $env:ProgramData "cloudflared"
$ConfigPath = Join-Path $DataDir "label-upload.yml"

function Assert-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]$identity
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "Run this script from an elevated PowerShell window."
    }
}

function Get-CloudflaredPath {
    $command = Get-Command cloudflared.exe -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $knownPath = "C:\Program Files (x86)\cloudflared\cloudflared.exe"
    if (Test-Path -LiteralPath $knownPath) {
        return $knownPath
    }

    throw "cloudflared.exe was not found."
}

function Get-Tunnel {
    param([string]$Cloudflared)

    $json = & $Cloudflared tunnel list --output json 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to list Cloudflare tunnels. Run 'cloudflared tunnel login' first."
    }

    return @($json | ConvertFrom-Json) | Where-Object { $_.name -eq $TunnelName } | Select-Object -First 1
}

function Install-TunnelService {
    Assert-Administrator
    $cloudflared = Get-CloudflaredPath
    $tunnel = Get-Tunnel -Cloudflared $cloudflared

    if (-not $tunnel) {
        & $cloudflared tunnel create $TunnelName
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to create tunnel '$TunnelName'."
        }
        $tunnel = Get-Tunnel -Cloudflared $cloudflared
    }

    $tunnelId = $tunnel.id
    $sourceCredentials = Join-Path $env:USERPROFILE ".cloudflared\$tunnelId.json"
    if (-not (Test-Path -LiteralPath $sourceCredentials)) {
        throw "Tunnel credentials not found at $sourceCredentials."
    }

    New-Item -ItemType Directory -Path $DataDir -Force | Out-Null
    $credentialsPath = Join-Path $DataDir "$tunnelId.json"
    Copy-Item -LiteralPath $sourceCredentials -Destination $credentialsPath -Force

    $config = @"
tunnel: $tunnelId
credentials-file: $credentialsPath

ingress:
  - hostname: $Hostname
    service: $Origin
  - service: http_status:404
"@
    Set-Content -LiteralPath $ConfigPath -Value $config -Encoding ascii

    # Credentials are readable only by SYSTEM and local administrators.
    & icacls.exe $DataDir /inheritance:r /grant:r "SYSTEM:(OI)(CI)F" "Administrators:(OI)(CI)F" | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to protect $DataDir."
    }

    & $cloudflared tunnel route dns --overwrite-dns $TunnelName $Hostname
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to route $Hostname to tunnel '$TunnelName'."
    }

    $existing = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($existing) {
        if ($existing.Status -ne "Stopped") {
            Stop-Service -Name $ServiceName -Force
        }
        & sc.exe delete $ServiceName | Out-Null
        Start-Sleep -Seconds 1
    }

    $binaryPath = '"{0}" --no-autoupdate tunnel --config "{1}" run' -f $cloudflared, $ConfigPath
    New-Service -Name $ServiceName -BinaryPathName $binaryPath -DisplayName "Cloudflare Tunnel - Label Upload" -StartupType Automatic | Out-Null
    & sc.exe failure $ServiceName reset= 86400 actions= restart/5000/restart/15000/restart/60000 | Out-Null
    & sc.exe failureflag $ServiceName 1 | Out-Null
    Start-Service -Name $ServiceName

    Write-Output "Installed and started $ServiceName."
    Write-Output "https://$Hostname -> $Origin"
}

function Show-Status {
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if (-not $service) {
        Write-Output "$ServiceName is not installed."
        return
    }

    $service | Select-Object Name, Status, StartType
    if (Test-Path -LiteralPath $ConfigPath) {
        Write-Output "Config: $ConfigPath"
    }
}

switch ($Action) {
    "Install" { Install-TunnelService }
    "Start" { Assert-Administrator; Start-Service -Name $ServiceName }
    "Stop" { Assert-Administrator; Stop-Service -Name $ServiceName }
    "Restart" { Assert-Administrator; Restart-Service -Name $ServiceName -Force }
    "Status" { Show-Status }
    "Uninstall" {
        Assert-Administrator
        $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        if ($service) {
            if ($service.Status -ne "Stopped") {
                Stop-Service -Name $ServiceName -Force
            }
            & sc.exe delete $ServiceName | Out-Null
        }
        Write-Output "Removed $ServiceName. The Cloudflare tunnel and DNS record were retained."
    }
}
