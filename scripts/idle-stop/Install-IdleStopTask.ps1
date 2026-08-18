#Requires -Version 5.1
<#
.SYNOPSIS
    Install the idle auto-stop Scheduled Task on this EC2 instance.

.DESCRIPTION
    Independent of the desktop client. Requires an instance profile that can
    call ec2:StopInstances on this instance only.
#>
[CmdletBinding()]
param(
    [string]$InstallDir = "$env:ProgramFiles\Ec2DesktopManager\idle-stop",
    [int]$IdleMinutes = 60
)

$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
$scriptSource = Join-Path $PSScriptRoot "Idle-Check.ps1"
Copy-Item -Path $scriptSource -Destination (Join-Path $InstallDir "Idle-Check.ps1") -Force

$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$InstallDir\Idle-Check.ps1`" -IdleMinutes $IdleMinutes"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 10) -RepetitionDuration ([TimeSpan]::MaxValue)
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
Register-ScheduledTask -TaskName "Ec2DesktopManagerIdleStop" -Action $action -Trigger $trigger -Principal $principal -Force | Out-Null
Write-Host "Installed Scheduled Task Ec2DesktopManagerIdleStop (every 10 minutes, idle after $IdleMinutes minutes)."
