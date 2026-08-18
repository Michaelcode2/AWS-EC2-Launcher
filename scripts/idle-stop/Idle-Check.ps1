#Requires -Version 5.1
<#
.SYNOPSIS
    Stop this EC2 instance after 60 minutes with no active Windows sessions.

.DESCRIPTION
    Runs on the instance via Scheduled Task. Uses the instance profile only.
    Do not put IAM access keys in this file. If session status or AWS is
    unavailable, the instance is left running.
#>
[CmdletBinding()]
param(
    [int]$IdleMinutes = 60,
    [string]$StateDirectory = "$env:ProgramData\Ec2DesktopManager",
    [string]$Region = ""
)

$ErrorActionPreference = "Stop"
$StateFile = Join-Path $StateDirectory "idle-state.json"
$LogFile = Join-Path $StateDirectory "idle-stop.log"

function Write-OpLog {
    param(
        [string]$Message,
        [ValidateSet("Information", "Warning", "Error")]
        [string]$Level = "Information"
    )
    $line = "{0:o} [{1}] {2}" -f (Get-Date).ToUniversalTime(), $Level, $Message
    try {
        if (-not (Test-Path $StateDirectory)) {
            New-Item -ItemType Directory -Path $StateDirectory -Force | Out-Null
        }
        Add-Content -Path $LogFile -Value $line -Encoding UTF8
    } catch {
        # Continue even if file logging fails.
    }
    try {
        if (-not [System.Diagnostics.EventLog]::SourceExists("Ec2DesktopManagerIdleStop")) {
            New-EventLog -LogName Application -Source "Ec2DesktopManagerIdleStop"
        }
        Write-EventLog -LogName Application -Source "Ec2DesktopManagerIdleStop" -EntryType $Level -EventId 1000 -Message $Message
    } catch {
        # Event log registration may require elevation on first run.
    }
}

function Get-ActiveSessionCount {
    try {
        $output = & quser 2>&1
        if ($LASTEXITCODE -ne 0 -and "$output" -notmatch "No User exists") {
            return $null
        }
        $text = ($output | Out-String)
        if ($text -match "No User exists") {
            return 0
        }
        $active = 0
        foreach ($line in @($output)) {
            $row = "$line"
            if ($row -match "USERNAME" -or $row -match "No User") {
                continue
            }
            if ($row -match "\bActive\b") {
                $active++
            }
        }
        return $active
    } catch {
        return $null
    }
}

function Get-InstanceId {
    try {
        $token = Invoke-RestMethod -Method PUT -Uri "http://169.254.169.254/latest/api/token" `
            -Headers @{ "X-aws-ec2-metadata-token-ttl-seconds" = "21600" } -TimeoutSec 3
        return Invoke-RestMethod -Uri "http://169.254.169.254/latest/meta-data/instance-id" `
            -Headers @{ "X-aws-ec2-metadata-token" = $token } -TimeoutSec 3
    } catch {
        return $null
    }
}

function Get-InstanceRegion {
    param([string]$Configured)
    if ($Configured) { return $Configured }
    try {
        $token = Invoke-RestMethod -Method PUT -Uri "http://169.254.169.254/latest/api/token" `
            -Headers @{ "X-aws-ec2-metadata-token-ttl-seconds" = "21600" } -TimeoutSec 3
        $az = Invoke-RestMethod -Uri "http://169.254.169.254/latest/meta-data/placement/availability-zone" `
            -Headers @{ "X-aws-ec2-metadata-token" = $token } -TimeoutSec 3
        return $az.Substring(0, $az.Length - 1)
    } catch {
        return $null
    }
}

function Read-LastActive {
    if (-not (Test-Path $StateFile)) {
        return $null
    }
    try {
        $json = Get-Content -Path $StateFile -Raw | ConvertFrom-Json
        return [datetime]::Parse($json.lastActive).ToUniversalTime()
    } catch {
        return $null
    }
}

function Write-LastActive {
    param([datetime]$When)
    if (-not (Test-Path $StateDirectory)) {
        New-Item -ItemType Directory -Path $StateDirectory -Force | Out-Null
    }
    @{ lastActive = $When.ToUniversalTime().ToString("o") } | ConvertTo-Json | Set-Content -Path $StateFile -Encoding UTF8
}

function Stop-LocalInstance {
    param([string]$InstanceId, [string]$AwsRegion)
    $aws = Get-Command aws -ErrorAction SilentlyContinue
    if (-not $aws) {
        throw "AWS CLI was not found on the instance."
    }
    & aws ec2 stop-instances --instance-ids $InstanceId --region $AwsRegion
    if ($LASTEXITCODE -ne 0) {
        throw "aws ec2 stop-instances failed with exit code $LASTEXITCODE"
    }
}

$active = Get-ActiveSessionCount
if ($null -eq $active) {
    Write-OpLog -Level Warning -Message "Session status could not be determined. Leaving instance running."
    exit 0
}

if ($active -gt 0) {
    Write-LastActive -When (Get-Date).ToUniversalTime()
    Write-OpLog -Message "Active sessions=$active. Updated last-active timestamp."
    exit 0
}

$lastActive = Read-LastActive
if ($null -eq $lastActive) {
    Write-LastActive -When (Get-Date).ToUniversalTime()
    Write-OpLog -Message "No active sessions and no timestamp. Recorded last-active as now."
    exit 0
}

$elapsed = (Get-Date).ToUniversalTime() - $lastActive
if ($elapsed.TotalMinutes -lt $IdleMinutes) {
    Write-OpLog -Message ("No active sessions. Idle {0:N1} minutes of {1}." -f $elapsed.TotalMinutes, $IdleMinutes)
    exit 0
}

$instanceId = Get-InstanceId
$awsRegion = Get-InstanceRegion -Configured $Region
if (-not $instanceId -or -not $awsRegion) {
    Write-OpLog -Level Warning -Message "Could not resolve instance identity. Leaving instance running."
    exit 0
}

try {
    Stop-LocalInstance -InstanceId $instanceId -AwsRegion $awsRegion
    Write-OpLog -Message "Stopped instance $instanceId after idle timeout."
} catch {
    Write-OpLog -Level Error -Message "AWS stop failed; leaving instance running. $_"
    exit 0
}
