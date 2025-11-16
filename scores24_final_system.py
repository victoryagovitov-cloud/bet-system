# -*- coding: utf-8 -*-
"""
🚀 ФИНАЛЬНАЯ СИСТЕМА СБОРА ДАННЫХ СО SCORES24

МЕТОДЫ:
1. MCP Browser - для получения списка матчей (быстро)
2. Selenium - для сбора детальной статистики (когда нужно)
3. Прямые URL - когда известны из MCP

АЛГОРИТМ:
1. MCP → Scores24 → получить список live-матчей
2. Найти нужный матч → извлечь URL
3. Selenium → открыть URL → собрать статистику
4. Вернуть данные для анализа
"""
import sys
import io
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class Scores24FinalCollector:
    """
    Финальная версия коллектора
    Принимает URL из MCP, собирает детальную статистику
    """
    
    def __init__(self, headless=True):
        self.driver = None
        self.headless = headless
    
    def _init_driver(self):
        """Ленивая инициализация драйвера"""
        if self.driver is None:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless")
            
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Оптимизация - отключаем картинки и видео
            prefs = {
                "profile.managed_default_content_settings.images": 2,
                "profile.managed_default_content_settings.media": 2,
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            try:
                import os
                os.environ['WDM_SSL_VERIFY'] = '0'
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
            except:
                service = Service("chromedriver.exe")
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(30)
    
    def collect_stats_from_url(self, match_url, team1, team2):
        """
        Собирает статистику по прямому URL (полученному из MCP)
        
        Args:
            match_url: URL страницы матча на Scores24
            team1, team2: названия команд (для контекста)
        
        Returns:
            dict: статистика матча
        """
        print(f"\n📊 Сбор статистики: {team1} - {team2}")
        print(f"   URL: {match_url}")
        
        self._init_driver()
        
        try:
            # Открываем страницу
            self.driver.get(match_url)
            
            print(f"   ⏳ Загрузка (5 сек)...", end="", flush=True)
            time.sleep(5)
            print(" ✓")
            
            # Получаем HTML
            page_text = self.driver.page_source
            
            # Сохраняем для отладки
            debug_file = f"debug_{team1.replace(' ', '_')[:20]}.html"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(page_text)
            
            # Парсим статистику
            print(f"   📈 Парсинг данных...", end="", flush=True)
            
            stats = {
                'xg': self._extract_xg(page_text),
                'possession': self._extract_possession(page_text),
                'shots': self._extract_shots(page_text),
                'shots_on_target': self._extract_shots_on_target(page_text),
                'corners': self._extract_corners(page_text),
                'h2h': self._extract_h2h(page_text),
                'form_team1': self._extract_form(page_text, 1),
                'form_team2': self._extract_form(page_text, 2)
            }
            
            print(" ✓")
            
            # Выводим что собрали
            self._print_stats(stats)
            
            print(f"   ✅ Статистика собрана!\n")
            return stats
            
        except Exception as e:
            print(f"   ❌ Ошибка: {e}\n")
            return {}
    
    def _extract_xg(self, page_text):
        """Извлекает xG (Expected Goals)"""
        match = re.search(r'(\d+\.?\d*)\s+xG\s+(\d+\.?\d*)', page_text)
        if match:
            return f"{match.group(1)} - {match.group(2)}"
        return None
    
    def _extract_possession(self, page_text):
        """Извлекает владение мячом"""
        match = re.search(r'(\d+)%\s+Владение мячом\s+(\d+)%', page_text)
        if match:
            return f"{match.group(1)}% - {match.group(2)}%"
        return None
    
    def _extract_shots(self, page_text):
        """Извлекает удары"""
        match = re.search(r'(\d+)\s+Удары\s+(\d+)', page_text)
        if match:
            return f"{match.group(1)} - {match.group(2)}"
        return None
    
    def _extract_shots_on_target(self, page_text):
        """Извлекает удары в створ"""
        match = re.search(r'(\d+)\s+Удары в створ ворот\s+(\d+)', page_text)
        if match:
            return f"{match.group(1)} - {match.group(2)}"
        return None
    
    def _extract_corners(self, page_text):
        """Извлекает угловые"""
        match = re.search(r'(\d+)\s+Угловые\s+(\d+)', page_text)
        if match:
            return f"{match.group(1)} - {match.group(2)}"
        return None
    
    def _extract_h2h(self, page_text):
        """Извлекает историю встреч"""
        match = re.search(r'(\d+)%\s+(\d+)\s+Победа\s+(\d+)%\s+(\d+)\s+Ничьих\s+(\d+)%\s+(\d+)\s+Победа', page_text)
        if match:
            return {
                'team1_wins': int(match.group(2)),
                'draws': int(match.group(4)),
                'team2_wins': int(match.group(6)),
                'display': f"{match.group(2)}-{match.group(4)}-{match.group(6)}"
            }
        return None
    
    def _extract_form(self, page_text, team_number):
        """Извлекает форму команды"""
        # Находим все В/П/Н
        forms = re.findall(r'\s([ВПН])\s', page_text)
        
        if len(forms) >= 10:
            # Первые 5 - команда 1, следующие 5 - команда 2
            start = 0 if team_number == 1 else 5
            form = forms[start:start+5]
            
            if form:
                return {
                    'last_5': ''.join(form),
                    'wins': form.count('В'),
                    'draws': form.count('Н'),
                    'losses': form.count('П')
                }
        
        return None
    
    def _print_stats(self, stats):
        """Выводит собранную статистику"""
        if stats.get('xg'):
            print(f"\n      xG: {stats['xg']}")
        if stats.get('possession'):
            print(f"      Владение: {stats['possession']}")
        if stats.get('shots'):
            print(f"      Удары: {stats['shots']}")
        if stats.get('shots_on_target'):
            print(f"      В створ: {stats['shots_on_target']}")
        if stats.get('corners'):
            print(f"      Угловые: {stats['corners']}")
        if stats.get('h2h'):
            h2h = stats['h2h']
            print(f"      H2H: {h2h['display']}")
        if stats.get('form_team1'):
            print(f"      Форма 1: {stats['form_team1']['last_5']}")
        if stats.get('form_team2'):
            print(f"      Форма 2: {stats['form_team2']['last_5']}")
    
    def create_analysis_text(self, stats, match_data):
        """
        Создает КОРОТКИЙ и ИНФОРМАТИВНЫЙ текст анализа
        Максимум 1-2 предложения, только ключевые факты
        """
        parts = []
        
        # xG (если большая разница)
        if stats.get('xg'):
            parts.append(f"xG {stats['xg']}")
        
        # Владение (если > 55%)
        if stats.get('possession'):
            poss = stats['possession'].split('%')[0]
            if int(poss) > 55:
                parts.append(f"{poss}% владения")
        
        # H2H (если есть преимущество)
        if stats.get('h2h'):
            h2h = stats['h2h']
            if h2h['team1_wins'] > h2h['team2_wins']:
                parts.append(f"H2H {h2h['display']}")
        
        # Форма (если хорошая)
        form1 = stats.get('form_team1', {})
        if form1 and form1.get('wins', 0) >= 3:
            parts.append(f"форма {form1['last_5']}")
        
        # Собираем максимум 2 факта
        if parts:
            text = ', '.join(parts[:2])
        else:
            score = match_data.get('score', '?')
            text = f"Ведет {score}, контроль игры"
        
        return text.capitalize()
    
    def close(self):
        """Закрыть браузер"""
        if self.driver:
            self.driver.quit()
            print("🔧 Браузер закрыт\n")


# ===================== ИНТЕГРАЦИЯ С MCP =====================

def extract_match_urls_from_mcp_snapshot(snapshot_text, sport):
    """
    Извлекает URLs матчей из snapshot MCP Browser
    
    Args:
        snapshot_text: текст snapshot от mcp_browsermcp_browser_snapshot
        sport: 'football', 'tennis', 'handball'
    
    Returns:
        list: список dict с данными матчей и их URLs
    """
    print(f"\n🔍 Извлечение URLs из MCP snapshot ({sport})")
    
    matches = []
    
    # Ищем ссылки вида /ru/soccer/m-DATE-TEAM1-TEAM2
    sport_map = {'football': 'soccer', 'tennis': 'tennis', 'handball': 'handball'}
    sport_path = sport_map.get(sport, 'soccer')
    
    pattern = rf'/ru/{sport_path}/m-[\w-]+'
    urls = re.findall(pattern, snapshot_text)
    
    # Убираем дубликаты
    unique_urls = list(set(urls))
    
    print(f"   ✅ Найдено URLs: {len(unique_urls)}")
    
    for url in unique_urls:
        # Извлекаем названия команд из URL
        parts = url.split('/')[-1].replace('m-', '').split('-')
        
        if len(parts) >= 5:  # Минимум: DD-MM-YYYY-team1-team2
            full_url = f"https://scores24.live{url}"
            matches.append({
                'url': full_url,
                'url_slug': url
            })
    
    return matches


# ===================== ГЛАВНАЯ ФУНКЦИЯ =====================

def analyze_matches_with_scores24(matches, use_selenium=True):
    """
    Анализирует список матчей через Scores24
    
    Args:
        matches: список матчей с URLs из MCP
        use_selenium: использовать ли Selenium для детальной статистики
    
    Returns:
        list: матчи с собранной статистикой
    """
    print("\n" + "="*70)
    print("📊 АНАЛИЗ МАТЧЕЙ ЧЕРЕЗ SCORES24")
    print("="*70 + "\n")
    
    if not use_selenium:
        print("⚠️ Режим без Selenium - только базовая проверка\n")
        return matches
    
    print(f"Матчей для анализа: {len(matches)}\n")
    
    collector = Scores24FinalCollector(headless=True)
    results = []
    
    try:
        for i, match in enumerate(matches, 1):
            print(f"[{i}/{len(matches)}] {match.get('team1', '?')} - {match.get('team2', '?')}")
            
            # Если есть URL - используем его
            if match.get('scores24_url'):
                stats = collector.collect_stats_from_url(
                    match['scores24_url'],
                    match.get('team1', ''),
                    match.get('team2', '')
                )
                
                # Создаем текст анализа
                analysis_text = collector.create_analysis_text(stats, match)
                
                # Добавляем к матчу
                match['scores24_stats'] = stats
                match['analysis_text'] = analysis_text
                match['verified_on_scores24'] = True
                
                results.append(match)
            else:
                print(f"   ⚠️ Нет URL для проверки")
                results.append(match)
            
            # Небольшая пауза между матчами
            if i < len(matches):
                time.sleep(2)
    
    finally:
        collector.close()
    
    print("="*70)
    print(f"✅ Анализ завершен: {len(results)} матчей")
    print("="*70 + "\n")
    
    return results


# ===================== ТЕСТ =====================

def test_with_known_urls():
    """Тест с известными URLs (из MCP Browser)"""
    print("\n" + "="*70)
    print("🧪 ТЕСТ СИСТЕМЫ С ИЗВЕСТНЫМИ URLs")
    print("="*70 + "\n")
    
    # URLs матчей, которые мы видели через MCP
    test_matches = [
        {
            'team1': 'Боруссия Менхенгладбах',
            'team2': 'Карлсруэ',
            'league': 'Германия. Кубок',
            'score': '2:0',
            'odds': 1.20,
            'scores24_url': 'https://scores24.live/ru/soccer/m-28-10-2025-borussia-m-gladbach-karlsruher'
        },
        {
            'team1': 'Спортинг',
            'team2': 'Алверка',
            'league': 'Португалия. Кубок лиги',
            'score': '2:0',
            'odds': 1.01,
            'scores24_url': 'https://scores24.live/ru/soccer/m-29-10-2025-sporting-lisbon-alverca'
        },
        {
            'team1': 'Сьон',
            'team2': 'Санкт-Галлен',
            'league': 'Швейцария. Суперлига',
            'score': '3:1',
            'odds': 1.05,
            'scores24_url': 'https://scores24.live/ru/soccer/m-29-10-2025-sion-st-gallen-1879-'
        },
        {
            'team1': 'Нанси',
            'team2': 'Бастия',
            'league': 'Франция. Лига 2',
            'score': '1:0',
            'odds': 1.27,
            'scores24_url': 'https://scores24.live/ru/soccer/m-28-10-2025-nancy-bastia-1'
        }
    ]
    
    # Анализируем
    results = analyze_matches_with_scores24(test_matches, use_selenium=True)
    
    # Выводим результаты
    print("\n" + "="*70)
    print("📋 ИТОГОВАЯ СТАТИСТИКА ПО МАТЧАМ")
    print("="*70 + "\n")
    
    for i, match in enumerate(results, 1):
        print(f"{i}. {match['team1']} - {match['team2']}")
        print(f"   Счет: {match['score']}, Коэфф: {match['odds']}")
        
        if match.get('analysis_text'):
            print(f"   📌 {match['analysis_text']}")
        
        stats = match.get('scores24_stats', {})
        if stats.get('xg'):
            print(f"   xG: {stats['xg']}")
        
        print()
    
    print("="*70)
    print("✅ ТЕСТ ЗАВЕРШЕН")
    print("="*70 + "\n")


if __name__ == "__main__":
    test_with_known_urls()

