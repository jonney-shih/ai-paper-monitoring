# Create (or update) the daily scheduled task on THIS computer.
# Usage (PowerShell, run once per computer):
#   powershell -ExecutionPolicy Bypass -File .\setup_schedule.ps1            # daily 08:00
#   powershell -ExecutionPolicy Bypass -File .\setup_schedule.ps1 -Time 07:30
#   powershell -ExecutionPolicy Bypass -File .\setup_schedule.ps1 -Remove    # delete the task
# Keep this file ASCII-only (Windows PowerShell 5.1 reads BOM-less files as ANSI).
param(
    [string]$Time = "08:00",
    [string]$TaskName = "AI-Paper-Monitoring-Daily",
    [switch]$Remove
)

if ($Remove) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "Removed task $TaskName"
    return
}

$vbs = Join-Path $PSScriptRoot "run_daily.vbs"
if (-not (Test-Path $vbs)) { throw "run_daily.vbs not found next to this script: $vbs" }

$action   = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$vbs`""
$trigger  = New-ScheduledTaskTrigger -Daily -At $Time
# StartWhenAvailable: run after wake-up/boot if the computer was off at the scheduled time
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings `
    -Description "Run AI paper monitoring daily" -Force | Out-Null

$info = Get-ScheduledTaskInfo $TaskName
Write-Host "Task '$TaskName' is set. Next run: $($info.NextRunTime)"
Write-Host "Test it now with:  Start-ScheduledTask $TaskName"
