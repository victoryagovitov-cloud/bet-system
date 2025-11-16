#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генерация визитной карточки системы - красивая статистика для демонстрации
"""

from results_tracker import get_statistics
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

def generate_performance_card():
    """Генерирует визитную карточку системы с акцентом на ROI."""
    
    stats = get_statistics()
    
    if stats['total_bets'] == 0:
        return "Нет данных для отображения"
    
    # Рассчитываем дополнительные метрики
    avg_coefficient = stats['total_payout'] / stats['total_stake'] if stats['total_stake'] > 0 else 0
    avg_profit_per_bet = stats['total_profit'] / stats['total_bets'] if stats['total_bets'] > 0 else 0
    profit_margin = (stats['total_profit'] / stats['total_payout'] * 100) if stats['total_payout'] > 0 else 0
    
    # Форматируем ROI с акцентом
    roi_formatted = f"{stats['roi']:.2f}%"
    if stats['roi'] > 5:
        roi_status = "🔥 ОТЛИЧНО"
    elif stats['roi'] > 2:
        roi_status = "✅ ХОРОШО"
    elif stats['roi'] > 0:
        roi_status = "📈 ПОЛОЖИТЕЛЬНО"
    else:
        roi_status = "⚠️ ОТРИЦАТЕЛЬНО"
    
    card = []
    card.append("=" * 70)
    card.append("🎯 ВИЗИТНАЯ КАРТОЧКА СИСТЕМЫ LIVE-СТАВОК")
    card.append("=" * 70)
    card.append("")
    
    # Главный показатель - ROI
    card.append("💰 ГЛАВНЫЙ ПОКАЗАТЕЛЬ: ROI")
    card.append("-" * 70)
    card.append(f"ROI: {roi_formatted} {roi_status}")
    card.append(f"Прибыль: {stats['total_profit']:.2f} руб")
    card.append(f"Общая ставка: {stats['total_stake']:.2f} руб")
    card.append(f"Общий выигрыш: {stats['total_payout']:.2f} руб")
    card.append("")
    
    # Ключевые метрики
    card.append("📊 КЛЮЧЕВЫЕ МЕТРИКИ")
    card.append("-" * 70)
    card.append(f"Всего ставок: {stats['total_bets']}")
    card.append(f"Винрейт: {stats['win_rate']:.2f}%")
    card.append(f"Выигрышей: {stats['wins']}")
    card.append(f"Проигрышей: {stats['losses']}")
    card.append(f"Средний коэффициент: {avg_coefficient:.3f}")
    card.append(f"Средняя прибыль на ставку: {avg_profit_per_bet:.2f} руб")
    card.append(f"Маржа прибыли: {profit_margin:.2f}%")
    card.append("")
    
    # Статистика по видам спорта с ROI
    if stats['by_sport']:
        card.append("⚽🎾🤾 СТАТИСТИКА ПО ВИДАМ СПОРТА")
        card.append("-" * 70)
        
        # Сортируем по прибыли (убыванию)
        sorted_sports = sorted(
            stats['by_sport'].items(),
            key=lambda x: x[1]['profit'],
            reverse=True
        )
        
        for sport, data in sorted_sports:
            sport_emoji = {
                'football': '⚽',
                'tennis': '🎾',
                'handball': '🤾',
                'basketball': '🏀'
            }.get(sport.lower(), '📊')
            
            sport_roi = (data['profit'] / data['stake'] * 100) if data['stake'] > 0 else 0
            
            card.append(f"{sport_emoji} {sport.upper()}:")
            card.append(f"  Ставок: {data['bets']}")
            card.append(f"  Винрейт: {data['win_rate']:.2f}%")
            card.append(f"  ROI: {sport_roi:.2f}%")
            card.append(f"  Прибыль: {data['profit']:.2f} руб")
            card.append(f"  Ставка: {data['stake']:.2f} руб")
            card.append(f"  Выигрыш: {data['payout']:.2f} руб")
            card.append("")
    
    # Анализ эффективности
    card.append("📈 АНАЛИЗ ЭФФЕКТИВНОСТИ")
    card.append("-" * 70)
    
    if stats['roi'] > 5:
        card.append("✅ ROI превышает 5% - отличная результативность!")
    elif stats['roi'] > 2:
        card.append("✅ ROI выше 2% - стабильная прибыльность")
    elif stats['roi'] > 0:
        card.append("📊 ROI положительный - система работает")
    else:
        card.append("⚠️ ROI отрицательный - требуется оптимизация")
    
    if stats['win_rate'] > 95:
        card.append("✅ Винрейт выше 95% - исключительное качество отбора")
    elif stats['win_rate'] > 90:
        card.append("✅ Винрейт выше 90% - высокое качество отбора")
    elif stats['win_rate'] > 80:
        card.append("📊 Винрейт выше 80% - хорошее качество отбора")
    
    card.append("")
    card.append("=" * 70)
    card.append(f"Дата обновления: {datetime.now(ZoneInfo('Europe/Moscow')).strftime('%Y-%m-%d %H:%M:%S')}")
    card.append("=" * 70)
    
    return "\n".join(card)

def generate_short_card():
    """Генерирует краткую версию визитной карточки для быстрого просмотра."""
    
    stats = get_statistics()
    
    if stats['total_bets'] == 0:
        return "Нет данных"
    
    card = []
    card.append("🎯 СИСТЕМА LIVE-СТАВОК")
    card.append("─" * 50)
    card.append(f"💰 ROI: {stats['roi']:.2f}%")
    card.append(f"📊 Винрейт: {stats['win_rate']:.2f}%")
    card.append(f"✅ Ставок: {stats['total_bets']} | Выигрышей: {stats['wins']} | Проигрышей: {stats['losses']}")
    card.append(f"💵 Прибыль: {stats['total_profit']:.2f} руб")
    card.append("─" * 50)
    
    return "\n".join(card)

def main():
    # Полная визитная карточка
    full_card = generate_performance_card()
    
    # Сохраняем в файл
    card_file = Path("data/performance_card.txt")
    card_file.parent.mkdir(parents=True, exist_ok=True)
    with card_file.open("w", encoding="utf-8") as f:
        f.write(full_card)
    
    print(f"[OK] Визитная карточка сохранена в: {card_file}")
    
    # Краткая версия
    short_card = generate_short_card()
    
    # Сохраняем краткую версию
    short_file = Path("data/performance_card_short.txt")
    with short_file.open("w", encoding="utf-8") as f:
        f.write(short_card)
    
    print(f"[OK] Краткая версия сохранена в: {short_file}")
    
    # Выводим ключевые показатели без эмодзи
    stats = get_statistics()
    print(f"\nКлючевые показатели:")
    print(f"  ROI: {stats['roi']:.2f}%")
    print(f"  Винрейт: {stats['win_rate']:.2f}%")
    print(f"  Прибыль: {stats['total_profit']:.2f} руб")
    print(f"  Ставок: {stats['total_bets']}")

if __name__ == "__main__":
    main()

