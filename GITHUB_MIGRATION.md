# Миграция в GitHub

## План действий

1. ✅ Git репозиторий инициализирован
2. ✅ .gitignore настроен
3. ⏳ Определить основные файлы для коммита
4. ⏳ Создать первый коммит
5. ⏳ Создать GitHub репозиторий
6. ⏳ Настроить remote и запушить

## Основные файлы системы

### Критически важные (обязательно в репозитории):
- `generate_live_report.py` - генерация отчетов
- `graphql_live_analyzer.py` - анализ футбола
- `graphql_tennis_analyzer.py` - анализ тенниса
- `graphql_handball_analyzer.py` - анализ гандбола
- `scores24_graphql_client.py` - клиент GraphQL
- `scores24_snapshot_enricher.py` - обогащение через snapshot
- `send_live_report.py` - отправка в Telegram
- `auto_cycle_scheduler.py` - планировщик
- `recommendation_logger.py` - логирование рекомендаций
- `telegram_simple.py` - модуль Telegram
- `requirements.txt` - зависимости
- `config.json` - конфигурация (БЕЗ токенов!)
- `ПОЛНЫЙ_АЛГОРИТМ_РАБОТЫ.md` - документация

### Важные (документация):
- Все `.md` файлы с инструкциями
- `README.md` - главный README

### Исключить из репозитория:
- `data/recommendations_log.csv` - данные (уже в .gitignore)
- `logs/` - логи (уже в .gitignore)
- `.auto_cycle.lock` - lock файлы (уже в .gitignore)
- Тестовые скрипты (`test_*.py`, `debug_*.py`, `check_*.py`) - можно исключить или оставить
- Временные файлы

## Следующие шаги

1. Создать README.md с описанием проекта
2. Добавить основные файлы в git
3. Создать первый коммит
4. Создать GitHub репозиторий (через веб-интерфейс)
5. Настроить remote и запушить

