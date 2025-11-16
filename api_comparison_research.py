"""
Скрипт для исследования тарифов и ограничений API-SPORTS и ProSportsAPI
Создаёт сравнительную таблицу для принятия решения о резервных источниках данных
"""

import json
from datetime import datetime
from typing import Dict, List

def create_api_comparison_table() -> Dict:
    """Создаёт структуру для сравнения API провайдеров"""
    
    comparison = {
        "generated_at": datetime.now().isoformat(),
        "apis": {
            "api-sports": {
                "name": "API-SPORTS (api-football.com)",
                "website": "https://www.api-football.com",
                "github": "https://github.com/api-sports",
                "pricing_notes": "Требует проверки актуальных тарифов на сайте",
                "sports_covered": [
                    "Футбол (football)",
                    "Баскетбол (basketball)", 
                    "Бейсбол (baseball)",
                    "Американский футбол (american-football)",
                    "Хоккей (hockey)",
                    "Теннис (tennis)",
                    "Волейбол (volleyball)",
                    "Гандбол (handball)"
                ],
                "data_types": [
                    "Live матчи",
                    "Пре-матч данные",
                    "Исторические данные",
                    "Статистика команд",
                    "Статистика игроков",
                    "Турнирные таблицы",
                    "Коэффициенты букмекеров"
                ],
                "api_format": "REST API + GraphQL (частично)",
                "authentication": "API key в заголовке x-rapidapi-key или x-api-key",
                "sdk_available": [
                    "Python",
                    "JavaScript/Node.js",
                    ".NET",
                    "Ruby",
                    "CLI инструменты"
                ],
                "free_tier": {
                    "available": True,
                    "notes": "Ограниченное количество запросов, задержка обновлений"
                },
                "paid_tiers": {
                    "notes": "Различные уровни с увеличением лимитов запросов"
                },
                "rate_limits": "Зависит от тарифа (требует уточнения)",
                "handball_support": True,
                "tennis_support": True,
                "live_data_quality": "Высокая (требует проверки)",
                "legal_requirements": "Требуется указание источника данных",
                "pros": [
                    "Широкое покрытие видов спорта",
                    "Готовые SDK",
                    "Поддержка гандбола и тенниса",
                    "Хорошая документация"
                ],
                "cons": [
                    "Платные тарифы могут быть дорогими",
                    "Требование указания источника",
                    "Необходимость проверки актуальных лимитов"
                ],
                "use_case_for_us": "Резервный источник live-данных на случай проблем с Scores24, расширение на новые виды спорта"
            },
            "prosportsapi": {
                "name": "ProSportsAPI",
                "website": "https://prosportsapi.com",
                "github": "https://github.com/ProSportsAPI",
                "pricing_notes": "Требует проверки актуальных тарифов на сайте, возможны custom packages",
                "sports_covered": [
                    "Футбол (football)",
                    "Крикет (cricket)",
                    "Баскетбол (basketball)",
                    "Другие виды спорта (требует уточнения)"
                ],
                "data_types": [
                    "Live матчи",
                    "Исторические данные",
                    "Статистика команд",
                    "Статистика игроков",
                    "Турнирные таблицы",
                    "Fantasy points"
                ],
                "api_format": "REST API (JSON)",
                "authentication": "API key через личный кабинет",
                "sdk_available": [
                    "Ограниченная поддержка SDK",
                    "Основной формат - REST API"
                ],
                "free_tier": {
                    "available": True,
                    "notes": "Ограниченное количество запросов"
                },
                "paid_tiers": {
                    "notes": "Custom packages, гибкие тарифы"
                },
                "rate_limits": "Не указаны публично (требует запроса)",
                "handball_support": "Требует проверки",
                "tennis_support": "Требует проверки",
                "live_data_quality": "Требует проверки",
                "legal_requirements": "Требует проверки",
                "pros": [
                    "Возможны более гибкие тарифы",
                    "24/7 поддержка (заявлено)",
                    "Custom packages"
                ],
                "cons": [
                    "Меньше информации в открытом доступе",
                    "Меньше готовых SDK",
                    "Требует проверки покрытия видов спорта"
                ],
                "use_case_for_us": "Альтернативный источник, если предложат выгодные условия"
            }
        },
        "recommendations": {
            "immediate_action": [
                "Проверить актуальные тарифы на сайтах api-football.com и prosportsapi.com",
                "Запросить пробные API ключи для тестирования",
                "Сравнить стоимость для наших потребностей (live-данные, гандбол, теннис)",
                "Проверить юридические требования (attribution, лицензии)"
            ],
            "integration_priority": "Низкий (резервный источник на случай проблем с Scores24)",
            "testing_approach": [
                "Получить тестовые ключи",
                "Проверить скорость ответа API",
                "Сравнить качество данных с Scores24",
                "Оценить покрытие гандбола и тенниса"
            ]
        }
    }
    
    return comparison

def save_comparison_table(filename: str = "data/api_comparison.json"):
    """Сохраняет таблицу сравнения в JSON"""
    comparison = create_api_comparison_table()
    
    import os
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(comparison, f, ensure_ascii=False, indent=2)
    
    print(f"[OK] Таблица сравнения сохранена в {filename}")
    return comparison

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    comparison = save_comparison_table()
    print("\n[OK] Сравнительная таблица API провайдеров создана")
    print(f"   - API-SPORTS: {len(comparison['apis']['api-sports']['sports_covered'])} видов спорта")
    print(f"   - ProSportsAPI: {len(comparison['apis']['prosportsapi']['sports_covered'])} видов спорта (требует уточнения)")
    print("\n[INFO] Следующие шаги:")
    for step in comparison['recommendations']['immediate_action']:
        print(f"   • {step}")

