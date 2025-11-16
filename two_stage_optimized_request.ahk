; ДВУХЭТАПНЫЙ ОПТИМИЗИРОВАННЫЙ ЗАПРОС
; Этап 1: Auto (сбор данных) - дешево
; Этап 2: Claude 4 (анализ) - качественно

#Persistent
SetTimer, CheckAndSend, 60000
return

CheckAndSend:
    FormatTime, CurrentHour, , HH
    FormatTime, CurrentMinute, , mm
    
    if (CurrentHour < 9 or CurrentHour > 23)
        return
    if (CurrentHour = 23 and CurrentMinute > 30)
        return
    
    if (CurrentMinute = 0 or CurrentMinute = 45)
    {
        FormatTime, TimeStamp, , HH:mm
        FormatTime, FullTime, , dd.MM.yyyy HH:mm:ss
        
        ; ═══════════════════════════════════════
        ; ЭТАП 1: СБОР ДАННЫХ (МОДЕЛЬ: AUTO)
        ; ═══════════════════════════════════════
        
        Stage1Text := "🌐 СБОР ДАННЫХ BetBoom - " . TimeStamp . " МСК`n`n"
        Stage1Text .= "📋 Инструкции: CACHED_INSTRUCTIONS.txt`n`n"
        Stage1Text .= "🎯 ЗАДАЧА:`n"
        Stage1Text .= "1️⃣ BetBoom snapshot (футбол/теннис/гандбол)`n"
        Stage1Text .= "2️⃣ Prefilter: неничейные, коэф≤2.5, фаворит ведет`n"
        Stage1Text .= "3️⃣ Scores24 для каждого отобранного (xG, %, H2H)`n"
        Stage1Text .= "4️⃣ Сохрани результат в: raw_data_cache.json`n"
        Stage1Text .= "   Формат: JSON с матчами, статистикой, коэффициентами`n`n"
        Stage1Text .= "⏰ " . FullTime . " МСК`n"
        Stage1Text .= "🤖 Используй модель: AUTO (простой сбор данных)"
        
        ; Отправляем Этап 1
        SendStage1(Stage1Text)
        
        ; Ждем завершения сбора (примерно 2-3 минуты)
        Sleep, 180000
        
        ; Проверяем наличие файла данных
        IfExist, raw_data_cache.json
        {
            ; ═══════════════════════════════════════
            ; ЭТАП 2: АНАЛИЗ (МОДЕЛЬ: CLAUDE 4)
            ; ═══════════════════════════════════════
            
            Stage2Text := "🔍 АНАЛИЗ ДАННЫХ - " . TimeStamp . " МСК`n`n"
            Stage2Text .= "📊 Источник: raw_data_cache.json (прочитай)`n`n"
            Stage2Text .= "🎯 ЗАДАЧА:`n"
            Stage2Text .= "1️⃣ Проанализируй статистику (xG, владение, H2H)`n"
            Stage2Text .= "2️⃣ Рассчитай вероятность для каждого матча`n"
            Stage2Text .= "3️⃣ Сформируй прогнозы (только с реальными данными)`n"
            Stage2Text .= "4️⃣ Сохрани для ML (prediction_logger_ml.py)`n"
            Stage2Text .= "5️⃣ Отправь в Telegram (@TrueLiveBet)`n`n"
            Stage2Text .= "📋 Инструкции: ANALYSIS_INSTRUCTIONS.md`n"
            Stage2Text .= "🚨 Критично: используй ТОЛЬКО данные из Scores24!`n`n"
            Stage2Text .= "⏰ " . FullTime . " МСК`n"
            Stage2Text .= "🤖 Используй модель: CLAUDE 4 (анализ и прогноз)"
            
            ; Отправляем Этап 2
            SendStage2(Stage2Text)
        }
        else
        {
            ; Если нет данных - отправляем сообщение об ошибке
            ErrorText := "⚠️ ОШИБКА: raw_data_cache.json не найден`n"
            ErrorText .= "Проверь Этап 1 (сбор данных)`n"
            ErrorText .= "⏰ " . FullTime . " МСК"
            
            SendStage2(ErrorText)
        }
        
        ; Ждем 59 секунд чтобы не отправить дважды
        Sleep, 59000
    }
return

SendStage1(Text) {
    Clipboard := Text
    Sleep, 300
    WinActivate, ahk_exe Cursor.exe
    Sleep, 500
    
    Click, 1098, 1362
    Sleep, 300
    Click, 1098, 1362
    Sleep, 500
    
    Send, ^a
    Sleep, 200
    Send, ^v
    Sleep, 1000
    
    ; ВНИМАНИЕ: Перед отправкой нужно вручную выбрать модель AUTO
    ; Или добавить автоматический выбор через UI (сложнее)
    Send, {Enter}
    Sleep, 1000
}

SendStage2(Text) {
    Clipboard := Text
    Sleep, 300
    WinActivate, ahk_exe Cursor.exe
    Sleep, 500
    
    Click, 1098, 1362
    Sleep, 300
    Click, 1098, 1362
    Sleep, 500
    
    Send, ^a
    Sleep, 200
    Send, ^v
    Sleep, 1000
    
    ; ВНИМАНИЕ: Перед отправкой нужно вручную выбрать модель CLAUDE 4
    ; Или добавить автоматический выбор через UI (сложнее)
    Send, {Enter}
    Sleep, 1000
}

; Горячая клавиша для ручного запуска двух этапов (Ctrl+Shift+Y)
^+y::
    FormatTime, TimeStamp, , HH:mm
    FormatTime, FullTime, , dd.MM.yyyy HH:mm:ss
    
    ; Запускаем Этап 1
    Stage1Text := "🌐 СБОР ДАННЫХ (ТЕСТ) - " . TimeStamp . " МСК`n`n"
    Stage1Text .= "📋 CACHED_INSTRUCTIONS.txt`n"
    Stage1Text .= "1️⃣ BetBoom → 2️⃣ Prefilter → 3️⃣ Scores24 → 4️⃣ raw_data_cache.json`n"
    Stage1Text .= "🤖 МОДЕЛЬ: AUTO`n"
    Stage1Text .= "⏰ " . FullTime . " МСК"
    
    SendStage1(Stage1Text)
    
    MsgBox, 0, Этап 1, Данные отправлены. Через 2-3 мин запусти Этап 2 (Ctrl+Shift+U)
return

; Горячая клавиша для Этапа 2 (Ctrl+Shift+U)
^+u::
    FormatTime, TimeStamp, , HH:mm
    FormatTime, FullTime, , dd.MM.yyyy HH:mm:ss
    
    IfExist, raw_data_cache.json
    {
        Stage2Text := "🔍 АНАЛИЗ (ТЕСТ) - " . TimeStamp . " МСК`n`n"
        Stage2Text .= "📊 raw_data_cache.json`n"
        Stage2Text .= "1️⃣ Анализ → 2️⃣ Прогноз → 3️⃣ ML → 4️⃣ Telegram`n"
        Stage2Text .= "📋 ANALYSIS_INSTRUCTIONS.md`n"
        Stage2Text .= "🤖 МОДЕЛЬ: CLAUDE 4`n"
        Stage2Text .= "⏰ " . FullTime . " МСК"
        
        SendStage2(Stage2Text)
    }
    else
    {
        MsgBox, 0, Ошибка, raw_data_cache.json не найден! Сначала запусти Этап 1.
    }
return

; Выход
^+q::
    ExitApp
return

