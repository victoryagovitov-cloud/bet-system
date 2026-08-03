$ErrorActionPreference = 'Continue'
$out = @()
try {
  Stop-ScheduledTask -TaskName 'AI Prime Cron' -ErrorAction SilentlyContinue
  Disable-ScheduledTask -TaskName 'AI Prime Cron' -ErrorAction Stop | Out-Null
  $a = Get-ScheduledTask -TaskName 'AI Prime Cron'
  $out += "OK Enabled=$($a.Settings.Enabled) State=$($a.State)"
} catch {
  $out += "FAIL $($_.Exception.Message)"
}
$out | Set-Content -Encoding UTF8 'D:\cursor\Backtothestart\AUDIT_REWRITE\_autostart_backup\stop_20260803_234118\elevated_disable.log'
