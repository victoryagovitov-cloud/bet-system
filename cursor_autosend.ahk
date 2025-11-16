; АВТОМАТИЧЕСКАЯ ОТПРАВКА В CURSOR CHAT
; Запуск каждые 45 минут с 9:00 до 23:30 МСК

#Persistent
SetTimer, CheckAndSend, 60000 ; Проверка каждую минуту
return

CheckAndSend:
    ; Получаем текущее время (московское +3 часа от UTC)
    FormatTime, CurrentHour, , HH
    FormatTime, CurrentMinute, , mm
    
    ; Проверяем рабочие часы (9:00-23:30)
    if (CurrentHour < 9 or CurrentHour > 23)
        return
    if (CurrentHour = 23 and CurrentMinute > 30)
        return
    
    ; Проверяем нужное время (каждые 45 минут: :00 и :45)
    if (CurrentMinute = 0 or CurrentMinute = 45)
    {
        ; Формируем КОРОТКИЙ текст запроса с КРИТИЧНЫМИ напоминаниями
        FormatTime, TimeStamp, , HH:mm
        FormatTime, FullTime, , dd.MM.yyyy HH:mm:ss
        
    ; УЛЬТРА-ЭКОНОМНЫЙ ЗАПРОС (99% экономия токенов!)
    RequestText := "🎯F"
        
        ; Копируем в буфер обмена
        Clipboard := RequestText
        Sleep, 300
        
        ; Активируем окно Cursor
        WinActivate, ahk_exe Cursor.exe
        Sleep, 500
        
        ; Находим поле ввода и отправляем (обновлено для Cursor 2.0)
        Click, 1098, 1362
        Sleep, 300
        Click, 1098, 1362
        Sleep, 500
        
        ; Вставляем текст
        Send, ^a
        Sleep, 200
        Send, ^v
        Sleep, 1000
        
        ; Отправляем
        Send, {Enter}
        Sleep, 1000
        
        ; Запуск одношагового сценария (старый режим, без батчей)
        ; Run, powershell -NoProfile -ExecutionPolicy Bypass -Command "cd D:\cursor\Backtothestart; python correct_analyzer_with_prefilter.py"
        
        ; Ждем 59 секунд чтобы не отправить дважды в ту же минуту
        Sleep, 59000
    }
return

; Горячая клавиша для ручной отправки (Ctrl+Shift+T)
^+t::
    FormatTime, TimeStamp, , HH:mm
    FormatTime, FullTime, , dd.MM.yyyy HH:mm:ss
    
    ; УЛЬТРА-ЭКОНОМНЫЙ ЗАПРОС (идентичный автоматическому)
    RequestText := "🎯F"
    
    Clipboard := RequestText
    Sleep, 300
    
    WinActivate, ahk_exe Cursor.exe
    Sleep, 500
    
    ; Обновлено для Cursor 2.0
    Click, 1098, 1362
    Sleep, 300
    Click, 1098, 1362
    Sleep, 500
    
    Send, ^a
    Sleep, 200
    Send, ^v
    Sleep, 1000
    Send, {Enter}
    Sleep, 1000
    
    ; Тестовый запуск одношагового сценария
    ; Run, powershell -NoProfile -ExecutionPolicy Bypass -Command "cd D:\cursor\Backtothestart; python correct_analyzer_with_prefilter.py"
return

; Горячая клавиша для выхода (Ctrl+Shift+Q)
^+q::
    MsgBox, Autosender ostanovlen
    ExitApp
return
