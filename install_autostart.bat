@echo off
REM Установка автозапуска системы через Task Scheduler
echo ========================================
echo Установка автозапуска системы
echo ========================================
echo.

REM Получаем полный путь к скрипту
set SCRIPT_DIR=%~dp0
set PYTHON_SCRIPT=%SCRIPT_DIR%auto_start_service.py
set BAT_FILE=%SCRIPT_DIR%start_reliable_system.bat

REM Проверяем существование файлов
if not exist "%PYTHON_SCRIPT%" (
    echo ОШИБКА: Файл auto_start_service.py не найден!
    pause
    exit /b 1
)

echo Создание задачи в Task Scheduler...
echo.

REM Создаем задачу для автозапуска
schtasks /create /tn "TrueLiveBet AutoStart" /tr "python \"%PYTHON_SCRIPT%\"" /sc onstart /ru SYSTEM /f >nul 2>&1

if %errorlevel% equ 0 (
    echo [OK] Задача создана успешно!
    echo.
    echo Задача будет запускаться при старте Windows.
    echo Имя задачи: TrueLiveBet AutoStart
    echo.
) else (
    echo [ОШИБКА] Не удалось создать задачу.
    echo Возможно, нужны права администратора.
    echo.
    echo Попробуйте запустить от имени администратора.
    echo.
)

REM Альтернативный вариант: добавление в автозагрузку
echo ========================================
echo Альтернативный вариант: автозагрузка
echo ========================================
echo.
echo Можно также добавить в автозагрузку Windows:
echo 1. Нажми Win+R
echo 2. Введи: shell:startup
echo 3. Создай ярлык на файл: %BAT_FILE%
echo.

pause

