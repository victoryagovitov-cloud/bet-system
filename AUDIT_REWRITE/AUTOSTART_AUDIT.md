# AUTOSTART_AUDIT — Автозапуски старого проекта

**Дата проверки:** 2026-08-03  
**Хост:** Windows 10 (`DESKTOP-BKHM6T2`)  
**Правило:** отключать только явно связанное с проектом ставок; при сомнении — не трогать.

---

## 1. Что проверено

| Место | Результат |
|---|---|
| User Startup | `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup` |
| Common Startup | `%ProgramData%\Microsoft\Windows\Start Menu\Programs\Startup` |
| Win32_StartupCommand | да |
| Task Scheduler (фильтр по путям/именам) | да |
| HKCU/HKLM Run + RunOnce | да |
| Services по имени проекта | не найдено |
| Desktop / Start Menu shortcuts с именами проекта | только Startup lnk |
| Реестр RunOnce | пусто |

---

## 2. Найдено (связанное с проектом)

### A. Startup shortcut — `TrueLiveBet_Scheduler.lnk`
- **Путь:** User Startup
- **Target:** `D:\cursor\!Backtothestart\start_daily_scheduler.bat`
- **WorkingDirectory:** `D:\cursor\!Backtothestart`
- **Связь:** явная (TrueLiveBet + путь к копии проекта)
- **Примечание:** target указывает на `\!Backtothestart\` (с `!`), не на текущий `D:\cursor\Backtothestart` — рассинхрон копий

### B. Task Scheduler — `AI Prime Cron`
- **State (на момент аудита):** Ready/Enabled = True
- **Action:** `D:\cursor\Backtothestart\ai_prime_cron.bat`
- **Trigger:** Daily с 2026-01-07 09:00, repetition pattern (фактически каждые ~5 мин в окне по комментариям bat)
- **Связь:** явная

### C. Task Scheduler — `PrematchScheduler`
- **State:** уже **Disabled**
- **Action:** `python D:\cursor\Backtothestart\prematch_scheduler.py`
- **Связь:** явная, но уже выключена

### D. Running process (не автозапуск, но живо)
- `python D:\cursor\Backtothestart\src\mcp\betboom_mcp_server.py` (PID 8868 на момент проверки)
- **Статус:** **требует подтверждения** перед kill

---

## 3. Найдено, но НЕ связано (не трогали)

| Элемент | Почему оставили |
|---|---|
| `Sidebar977.lnk` | Windows Sidebar gadgets |
| HKCU Run `proxy-sdk` | сторонний proxy SDK |
| HKCU Run `Teams` | Microsoft Teams |
| Google/Microsoft scheduled tasks | системные |

---

## 4. Что отключено

| Элемент | Действие | Откат |
|---|---|---|
| `TrueLiveBet_Scheduler.lnk` | **Перемещён** (не удалён) в `AUDIT_REWRITE/_autostart_backup/20260803_233254/TrueLiveBet_Scheduler.lnk` | См. `TrueLiveBet_Scheduler.RESTORE.txt` в той же папке |

Проверка после: в User Startup остались только `desktop.ini` и `Sidebar977.lnk`.

---

## 5. Что не удалось отключить (обновлено 2026-08-03 23:41)

Изначально Disable без elevation давал Access Denied.  
**После подтверждения пользователя (UAC):** задача `AI Prime Cron` успешно отключена elevated-скриптом.

| Элемент | Итог |
|---|---|
| Task `AI Prime Cron` | **Disabled** (Enabled=False, State=Disabled) |
| Process `betboom_mcp_server.py` PID 8868 | **Stopped** |
| Лог сессии | `AUDIT_REWRITE/_autostart_backup/stop_20260803_234118/STOP_ACTIONS.log` |

Экспорт задачи:  
`AUDIT_REWRITE/_autostart_backup/20260803_233254/AI_Prime_Cron_export.xml`

---

## 6. Требует ручной проверки / подтверждения

1. **Отключить `AI Prime Cron` от администратора** (критично — иначе парсер продолжит тикать).
2. **Остановить ли процесс `betboom_mcp_server.py`?** — связан со старым парсингом; kill не выполнялся без подтверждения.
3. Есть ли ещё копия проекта в `D:\cursor\!Backtothestart\` и её собственные автозапуски — путь из ярлыка.
4. Не зарегистрирован ли отдельный Windows Service вручную под другим именем (по имени TrueLive/Backtothestart — не найден).

---

## 7. Команды отката

### Вернуть Startup shortcut
```powershell
$src = 'D:\cursor\Backtothestart\AUDIT_REWRITE\_autostart_backup\20260803_233254\TrueLiveBet_Scheduler.lnk'
$dst = Join-Path ([Environment]::GetFolderPath('Startup')) 'TrueLiveBet_Scheduler.lnk'
Copy-Item -LiteralPath $src -Destination $dst
```

### Включить задачу снова (после успешного Disable)
```powershell
Enable-ScheduledTask -TaskName 'AI Prime Cron'
```

---

## 8. Рекомендация

После подтверждения пользователя:
1. Disable `AI Prime Cron` (admin).
2. Stop `betboom_mcp_server.py` и любые `start_production_stack*` процессы.
3. Не удалять bat-файлы из репозитория до завершения миграции — только автозапуск.
4. Не включать `prevent_windows_updates.bat` снова.
