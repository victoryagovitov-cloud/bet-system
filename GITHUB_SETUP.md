# Настройка GitHub репозитория

## Текущий статус

- ✅ Git репозиторий инициализирован
- ✅ `.gitignore` настроен
- ✅ `README.md` создан
- ⏳ Нет коммитов
- ⏳ Нет remote репозитория

## Следующие шаги

### Вариант 1: Создать новый репозиторий на GitHub

1. Создай репозиторий на GitHub (через веб-интерфейс)
2. Выполни команды:

```bash
# Добавить основные файлы
git add generate_live_report.py
git add graphql_*.py
git add scores24_*.py
git add send_live_report.py
git add auto_cycle_scheduler.py
git add recommendation_logger.py
git add config.json
git add requirements.txt
git add ПОЛНЫЙ_АЛГОРИТМ_РАБОТЫ.md
git add README.md
git add .gitignore

# Первый коммит
git commit -m "Initial commit: система анализа лайв-ставок"

# Подключить remote (замени URL на свой)
git remote add origin https://github.com/ТВОЙ_USERNAME/TrueLiveBet.git

# Отправить на GitHub
git branch -M main
git push -u origin main
```

### Вариант 2: Подключить существующий репозиторий

Если репозиторий уже создан:

```bash
git remote add origin https://github.com/ТВОЙ_USERNAME/TrueLiveBet.git
git branch -M main
git push -u origin main
```

## Важно

- **НЕ коммить** файлы с токенами (они в `.gitignore`)
- **НЕ коммить** логи и данные (`data/*.csv`, `logs/*.log`)
- **НЕ коммить** временные файлы (`.auto_cycle.lock`, `*.html`)

## Структура коммитов

Рекомендуется делать коммиты по функциональности:
- `feat: добавлена дедупликация матчей`
- `fix: исправлена фильтрация товарищеских матчей`
- `refactor: оптимизирован расчет доминирования`

