# -*- coding: utf-8 -*-
"""
🚀 ГИБРИДНАЯ СИСТЕМА: MCP BROWSER + ПАРСИНГ

ПРЕИМУЩЕСТВА:
- MCP Browser обходит защиту от ботов
- Быстрая навигация
- Полная статистика из snapshot
- Не нужен Selenium для Scores24

АЛГОРИТМ:
1. MCP → BetBoom → получить матчи
2. Для каждого матча:
   a) MCP → Scores24 (список) → найти матч
   b) MCP → клик на матч (или прямой URL)
   c) MCP → snapshot страницы матча
   d) Парсинг → извлечь статистику
3. Формирование рекомендации
4. Отправка в Telegram
"""
import re

class MCPScores24Parser:
    """
    Парсер статистики из MCP Browser snapshot
    """
    
    def parse_match_snapshot(self, snapshot_text):
        """
        Парсит snapshot страницы матча на Scores24
        
        Args:
            snapshot_text: текст от mcp_browsermcp_browser_snapshot
        
        Returns:
            dict: статистика матча
        """
        print("\n   📊 Парсинг snapshot...")
        
        stats = {
            'xg': self._extract_xg(snapshot_text),
            'possession': self._extract_possession(snapshot_text),
            'shots': self._extract_shots(snapshot_text),
            'shots_on_target': self._extract_shots_on_target(snapshot_text),
            'corners': self._extract_corners(snapshot_text),
            'h2h': self._extract_h2h(snapshot_text),
            'form': self._extract_forms(snapshot_text)
        }
        
        # Выводим что нашли
        self._print_stats(stats)
        
        return stats
    
    def _extract_xg(self, text):
        """xG (Expected Goals)"""
        match = re.search(r'(\d+\.?\d*)\s+xG\s+(\d+\.?\d*)', text)
        if match:
            return {'team1': float(match.group(1)), 'team2': float(match.group(2)), 'display': f"{match.group(1)} - {match.group(2)}"}
        return None
    
    def _extract_possession(self, text):
        """Владение мячом"""
        match = re.search(r'(\d+)%\s+Владение мячом\s+(\d+)%', text)
        if match:
            return {'team1': int(match.group(1)), 'team2': int(match.group(2)), 'display': f"{match.group(1)}% - {match.group(2)}%"}
        return None
    
    def _extract_shots(self, text):
        """Удары"""
        match = re.search(r'(\d+)\s+Удары\s+(\d+)', text)
        if match:
            return {'team1': int(match.group(1)), 'team2': int(match.group(2)), 'display': f"{match.group(1)} - {match.group(2)}"}
        return None
    
    def _extract_shots_on_target(self, text):
        """Удары в створ"""
        match = re.search(r'(\d+)\s+Удары в створ ворот\s+(\d+)', text)
        if match:
            return {'team1': int(match.group(1)), 'team2': int(match.group(2)), 'display': f"{match.group(1)} - {match.group(2)}"}
        return None
    
    def _extract_corners(self, text):
        """Угловые"""
        match = re.search(r'(\d+)\s+Угловые\s+(\d+)', text)
        if match:
            return {'team1': int(match.group(1)), 'team2': int(match.group(2)), 'display': f"{match.group(1)} - {match.group(2)}"}
        return None
    
    def _extract_h2h(self, text):
        """История встреч"""
        match = re.search(r'(\d+)%\s+(\d+)\s+Победа\s+(\d+)%\s+(\d+)\s+Ничьих\s+(\d+)%\s+(\d+)\s+Победа', text)
        if match:
            return {
                'team1_wins': int(match.group(2)),
                'draws': int(match.group(4)),
                'team2_wins': int(match.group(6)),
                'display': f"{match.group(2)}-{match.group(4)}-{match.group(6)}"
            }
        return None
    
    def _extract_forms(self, text):
        """Форма обеих команд (последние матчи)"""
        # Ищем все В/П/Н
        forms = re.findall(r'\s([ВПН])\s', text)
        
        if len(forms) >= 10:
            team1_form = ''.join(forms[:5])
            team2_form = ''.join(forms[5:10])
            
            return {
                'team1': {
                    'last_5': team1_form,
                    'wins': team1_form.count('В'),
                    'draws': team1_form.count('Н'),
                    'losses': team1_form.count('П')
                },
                'team2': {
                    'last_5': team2_form,
                    'wins': team2_form.count('В'),
                    'draws': team2_form.count('Н'),
                    'losses': team2_form.count('П')
                }
            }
        
        return None
    
    def _print_stats(self, stats):
        """Выводит собранную статистику"""
        found_any = False
        
        if stats.get('xg'):
            print(f"      ✓ xG: {stats['xg']['display']}")
            found_any = True
        if stats.get('possession'):
            print(f"      ✓ Владение: {stats['possession']['display']}")
            found_any = True
        if stats.get('shots'):
            print(f"      ✓ Удары: {stats['shots']['display']}")
            found_any = True
        if stats.get('shots_on_target'):
            print(f"      ✓ В створ: {stats['shots_on_target']['display']}")
            found_any = True
        if stats.get('corners'):
            print(f"      ✓ Угловые: {stats['corners']['display']}")
            found_any = True
        if stats.get('h2h'):
            print(f"      ✓ H2H: {stats['h2h']['display']}")
            found_any = True
        if stats.get('form'):
            print(f"      ✓ Форма 1: {stats['form']['team1']['last_5']}")
            print(f"      ✓ Форма 2: {stats['form']['team2']['last_5']}")
            found_any = True
        
        if not found_any:
            print(f"      ⚠️ Статистика не найдена в snapshot")
    
    def create_short_analysis(self, stats, match_data):
        """
        Создает КОРОТКИЙ анализ (1-2 предложения)
        """
        parts = []
        
        # xG (если большая разница)
        if stats.get('xg'):
            xg = stats['xg']
            if xg['team1'] > xg['team2'] * 1.5:
                parts.append(f"xG {xg['display']}")
        
        # Владение (если > 55%)
        if stats.get('possession'):
            poss = stats['possession']
            if poss['team1'] > 55:
                parts.append(f"{poss['team1']}% владения")
        
        # H2H
        if stats.get('h2h'):
            h2h = stats['h2h']
            if h2h['team1_wins'] > h2h['team2_wins']:
                parts.append(f"H2H {h2h['display']}")
        
        # Форма
        if stats.get('form'):
            form1 = stats['form']['team1']
            if form1['wins'] >= 3:
                parts.append(f"форма {form1['last_5']}")
        
        # Итог: максимум 2 факта
        if parts:
            return ', '.join(parts[:2])
        else:
            score = match_data.get('score', '?')
            return f"Ведет {score}, контроль матча"


# ===================== ПРИМЕР ИСПОЛЬЗОВАНИЯ С MCP =====================

def example_workflow_with_mcp():
    """
    ПРИМЕР: Как использовать с MCP Browser
    
    Это демонстрационная функция, показывающая алгоритм работы
    """
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║  🌐 АЛГОРИТМ РАБОТЫ С MCP BROWSER + SCORES24                        ║
╚══════════════════════════════════════════════════════════════════════╝

ШАГ 1: ПОЛУЧЕНИЕ МАТЧЕЙ С BETBOOM
──────────────────────────────────

1. mcp_browsermcp_browser_navigate(url="https://betboom.ru/sport/football?type=live")
2. snapshot = mcp_browsermcp_browser_snapshot()
3. Парсинг → список матчей + коэффициенты

Результат: [{team1, team2, score, odds, league}, ...]


ШАГ 2: ФИЛЬТРАЦИЯ НА BETBOOM
─────────────────────────────

Для каждого матча:
  ✓ Неничейный счет
  ✓ Фаворит ведет
  ✓ Коэффициент ≤ 2.5

Результат: отфильтрованный список (например, 4 матча из 96)


ШАГ 3: ПРОВЕРКА НА SCORES24 (ДЛЯ КАЖДОГО МАТЧА)
─────────────────────────────────────────────────

Для каждого отфильтрованного матча:

A) Открыть список на Scores24:
   mcp_browsermcp_browser_navigate(url="https://scores24.live/ru/soccer?matchesFilter=live")

B) Получить snapshot:
   snapshot = mcp_browsermcp_browser_snapshot()

C) Найти URL матча в snapshot:
   url = найти_в_snapshot(snapshot, team1, team2)
   # Пример: "/ru/soccer/m-28-10-2025-borussia-m-gladbach-karlsruher"

D) Перейти на страницу матча:
   mcp_browsermcp_browser_navigate(url=f"https://scores24.live{url}")

E) Подождать загрузки:
   mcp_browsermcp_browser_wait(time=5)

F) Получить snapshot страницы матча:
   match_snapshot = mcp_browsermcp_browser_snapshot()

G) Парсинг статистики:
   parser = MCPScores24Parser()
   stats = parser.parse_match_snapshot(match_snapshot)
   
   Извлечет:
   - xG (Expected Goals)
   - Владение мячом
   - Удары, удары в створ
   - Угловые
   - История встреч (H2H)
   - Форма команд

H) Создание анализа:
   analysis = parser.create_short_analysis(stats, match)
   
   Результат: "xG 1.7-0.45, 52% владения" или "H2H 3-1-2, форма ВВПНВ"


ШАГ 4: ФОРМИРОВАНИЕ СООБЩЕНИЯ
──────────────────────────────

Для каждого матча:
  - Название команд
  - Лига | Счет
  - Рекомендация П1 (коэфф)
  - 📌 {короткий анализ из статистики}
  - ✅ Категория ⭐⭐⭐⭐


ШАГ 5: ОТПРАВКА В TELEGRAM
──────────────────────────

Одно короткое сообщение со всеми матчами


╔══════════════════════════════════════════════════════════════════════╗
║  💡 КЛЮЧЕВОЙ МОМЕНТ                                                  ║
╚══════════════════════════════════════════════════════════════════════╝

MCP BROWSER МОЖЕТ ВСЁ:
✅ Открывать BetBoom (работает)
✅ Открывать Scores24 (работает)
✅ Получать snapshot с полными данными (работает)
❌ Selenium headless НЕ работает со Scores24 (защита от ботов)

РЕШЕНИЕ: Использовать ТОЛЬКО MCP Browser!
""")
    
    # Пример парсинга snapshot
    print("\n" + "="*70)
    print("🧪 ПРИМЕР ПАРСИНГА MCP SNAPSHOT")
    print("="*70 + "\n")
    
    # Пример snapshot (как будто от MCP)
    example_snapshot = """
    52% Владение мячом 48%
    1.7 xG 0.45
    17 Удары 7
    7 Удары в створ ворот 2
    7 Угловые 1
    50% 1 Победа 0% 0 Ничьих 50% 1 Победа
    Последние матчи
    В П Н В Н
    """
    
    parser = MCPScores24Parser()
    stats = parser.parse_match_snapshot(example_snapshot)
    
    print("\n📊 Результат парсинга:")
    for key, value in stats.items():
        if value:
            print(f"   ✓ {key}: {value}")
    
    # Пример создания анализа
    match_data = {'score': '2:0', 'odds': 1.20}
    analysis = parser.create_short_analysis(stats, match_data)
    
    print(f"\n📝 Итоговый анализ:")
    print(f"   '{analysis}'")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    example_workflow_with_mcp()

