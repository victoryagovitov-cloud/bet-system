# Run this script AS ADMINISTRATOR to disable AI Prime Cron
$ErrorActionPreference = "Stop"
$task = "AI Prime Cron"
Write-Host "Disabling scheduled task: $task"
Disable-ScheduledTask -TaskName $task | Out-Null
try { Stop-ScheduledTask -TaskName $task -ErrorAction SilentlyContinue } catch {}
$after = Get-ScheduledTask -TaskName $task
Write-Host "Result: Enabled=$($after.Settings.Enabled) State=$($after.State)"
pause
