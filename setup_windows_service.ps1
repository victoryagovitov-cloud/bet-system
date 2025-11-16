# PowerShell скрипт для установки автозапуска через Task Scheduler
# Запускать от имени администратора

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Установка автозапуска TrueLiveBet" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Получаем путь к скрипту
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonScript = Join-Path $ScriptDir "auto_start_service.py"
$PythonExe = (Get-Command python).Source

# Проверяем существование файла
if (-not (Test-Path $PythonScript)) {
    Write-Host "ОШИБКА: Файл auto_start_service.py не найден!" -ForegroundColor Red
    Write-Host "Путь: $PythonScript" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "Python: $PythonExe" -ForegroundColor Gray
Write-Host "Скрипт: $PythonScript" -ForegroundColor Gray
Write-Host ""

# Удаляем старую задачу, если существует
$TaskName = "TrueLiveBet AutoStart"
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($ExistingTask) {
    Write-Host "Удаление существующей задачи..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
}

# Создаем действие
$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument "`"$PythonScript`"" -WorkingDirectory $ScriptDir

# Создаем триггер (при запуске системы)
$Trigger = New-ScheduledTaskTrigger -AtStartup

# Настройки задачи
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable:$false

# Создаем задачу
try {
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Автоматический запуск системы TrueLiveBet" -RunLevel Highest
    
    Write-Host "[OK] Задача создана успешно!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Имя задачи: $TaskName" -ForegroundColor Cyan
    Write-Host "Триггер: При запуске Windows" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Для проверки выполните:" -ForegroundColor Yellow
    Write-Host "  Get-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Для удаления задачи:" -ForegroundColor Yellow
    Write-Host "  Unregister-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "[ОШИБКА] Не удалось создать задачу:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Убедитесь, что запускаете от имени администратора!" -ForegroundColor Yellow
    Write-Host ""
}

pause

