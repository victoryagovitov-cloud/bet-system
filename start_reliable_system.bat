@echo off
REM Запуск надежной системы с watchdog и планировщиком
echo ========================================
echo Запуск системы TrueLiveBet
echo ========================================
echo.

REM Создаем директорию для логов
if not exist logs mkdir logs

echo [1/2] Запуск Watchdog сервиса...
start "Watchdog Service" /MIN python watchdog_service.py

REM Ждем 3 секунды для инициализации
timeout /t 3 /nobreak >nul

echo [2/2] Запуск планировщика...
start "Scheduler" /MIN python auto_cycle_scheduler.py

echo.
echo ========================================
echo Система запущена!
echo ========================================
echo.
echo Компоненты:
echo   - Watchdog Service (автоперезапуск)
echo   - Scheduler (основной планировщик)
echo.
echo Логи: logs\auto_cycle.log, logs\watchdog.log
echo.
echo Для проверки статуса запусти: check_system_status.bat
echo.
pause

