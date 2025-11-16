@echo off
chcp 65001 >nul
echo ========================================
echo   🤖 ЗАПУСК РАБОЧЕГО АВТОКЛИКЕРА
echo ========================================
echo.
echo ⚠️  ВАЖНО:
echo 1. НЕ ЗАКРЫВАЙ окно Cursor
echo 2. Автокликер будет отправлять запросы каждые 45 минут
echo 3. Рабочие часы: 9:00-23:30 МСК
echo.
echo Запускаю...
echo.

python working_autoclicker.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ Ошибка запуска!
    echo Проверь:
    echo - Python установлен
    echo - pyautogui и pyperclip установлены
    echo   pip install pyautogui pyperclip schedule
    pause
)

