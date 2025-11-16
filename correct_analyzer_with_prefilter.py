# -*- coding: utf-8 -*-
"""
✅ ПРАВИЛЬНЫЙ АЛГОРИТМ:
1. BetBoom → получить ВСЕ live-матчи
2. Фильтр → убрать ничьи и запрещённые турниры
3. Scores24 → проверка статистики (один live-снимок + прямой URL)
4. Формирование блоков сообщений сразу после сбора статистики
5. Telegram → отправка с повторными попытками
6. ML файлы → сохранить данные для обучения (ПОСЛЕ отправки!)
7. Проверка результатов → обновить старые pending прогнозы (старше 90 мин)
"""
from scores24_mcp_connector import check_scores24_mcp, verify_match_in_snapshot, parse_match_stats_from_snapshot, format_stats_details
from betboom_mcp_connector import get_betboom_matches_mcp
from prediction_logger_ml import PredictionLoggerML
from ml_result_checker_mcp import check_pending_results_mcp
import requests
import urllib3
import json
import time
import os
from datetime import datetime
from pathlib import Path
import re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

with open('config.json', 'r', encoding='utf-8') as f:
    CONFIG = json.load(f)

BOT_TOKEN = CONFIG['notifications']['telegram']['bot_token']
CHANNEL = CONFIG['notifications']['telegram']['channel_username']

DISCLAIMER_FILE = Path('ДИСКЛЕЙМЕРЫ_ДЛЯ_СООБЩЕНИЙ.txt')
DISCLAIMER_STATE_FILE = Path('.disclaimer_state.json')

LEAGUE_WHITELIST_KEYWORDS = []

NATIONAL_TEAM_KEYWORDS = [
    'world cup', 'чемпионат мира', 'euro', 'евро', 'africa cup', 'кубок африки', 'copa america',
    'asian cup', 'кубок азии', 'gold cup', 'кубок кока-кола', 'oly', 'олимпи', 'uefa nations league'
]

LEAGUE_BLACKLIST_KEYWORDS = [
    'acl', 'afc champions league',
    '5x5', '5х5', '3x3', '3х3', '7x7', '7х7', 'футбол 5x5', 'мини-футбол 5х5',
    'women', 'жен', 'femenino', 'feminina', 'ladies', 'womens',
    'u23', 'u22', 'u21', 'u20', 'u19', 'u18', 'u17', 'youth', 'юнош', 'молод',
    'reserve', 'резерв',
    'third division', '3 division', '3rd division', 'third league', 'liga 3', 'лига 3', '3-я', '3-ю', 'третья',
    'fourth division', '4 division', '4th division', 'liga 4', 'лига 4', '4-я', 'четвертая', 'четвёртая'
]


def normalize_text(value: str) -> str:
    if not value:
        return ''
    return ' '.join(value.lower().replace('-', ' ').split())


def is_league_allowed(league_name: str, team1: str = '', team2: str = '') -> bool:
    league_norm = normalize_text(league_name)
    if not league_norm:
        return True

    for banned in LEAGUE_BLACKLIST_KEYWORDS:
        if banned in league_norm:
            return False

    for keyword in NATIONAL_TEAM_KEYWORDS:
        if keyword in league_norm:
            return True

    return True


def load_disclaimers():
    if not DISCLAIMER_FILE.exists():
        return []
    disclaimers = []
    buffer = []
    with DISCLAIMER_FILE.open('r', encoding='utf-8') as f:
        for raw_line in f:
            text = raw_line.strip()
            if not text:
                if buffer:
                    combined = ' '.join(buffer)
                    if re.match(r'^\d+\.\s', buffer[0]):
                        combined = re.sub(r'^\d+\.\s*', '', combined)
                        disclaimers.append(combined)
                    buffer = []
                continue
            if not buffer and not re.match(r'^\d+\.\s', text):
                continue
            buffer.append(text)
    if buffer:
        combined = ' '.join(buffer)
        if re.match(r'^\d+\.\s', buffer[0]):
            combined = re.sub(r'^\d+\.\s*', '', combined)
            disclaimers.append(combined)
    return disclaimers


def get_next_disclaimer():
    disclaimers = load_disclaimers()
    if not disclaimers:
        return "⚠️ Ставки — это риск. Играйте ответственно и в рамках своих возможностей."

    index = 0
    try:
        if DISCLAIMER_STATE_FILE.exists():
            with DISCLAIMER_STATE_FILE.open('r', encoding='utf-8') as f:
                state = json.load(f)
                index = (state.get('index', -1) + 1) % len(disclaimers)
        else:
            index = 0
    except Exception:
        index = 0

    try:
        DISCLAIMER_STATE_FILE.write_text(json.dumps({'index': index}, ensure_ascii=False), encoding='utf-8')
    except Exception:
        pass

    return disclaimers[index]

# ===================== ФИЛЬТРАЦИЯ НА BETBOOM =====================

def parse_score(score_str):
    """Парсит счет типа '2:0' или '1:1'"""
    try:
        if ':' not in score_str:
            return None, None
        
        parts = score_str.split(':')
        score1 = int(parts[0].strip())
        score2 = int(parts[1].split()[0].strip())  # "2 0" → 2
        return score1, score2
    except:
        return None, None

def is_draw(score_str):
    """Проверяет, ничья ли (футбол/гандбол). Для тенниса обрабатывается отдельно."""
    score1, score2 = parse_score(score_str)
    if score1 is None:
        return True  # Не смогли распарсить - считаем ничьей
    return score1 == score2

def prefilter_betboom_matches(all_matches):
    """
    ШАГ 1: Фильтрация на BetBoom ПЕРЕД проверкой на Scores24
    
    КРИТЕРИИ ОТБОРА:
    ✅ Неничейный счёт (только матчи, где кто-то ведет)
    ✅ Турнир не в черном списке (нет ACL, женских и т.д.)
    ✅ Остальное уходит на проверку статистики
    """
    print("\n" + "="*70)
    print("🔍 ШАГ 1: ФИЛЬТРАЦИЯ НА BETBOOM")
    print("="*70 + "\n")
    filtered = {'football': [], 'tennis': [], 'handball': []}
    candidate_rows = []
    stats = {
        'total': 0,
        'filtered_draw': 0,
        'filtered_league': 0,
        'filtered_other': 0,
        'passed': 0
    }
    
    enabled_sports = ['football']
    for sport in ['football', 'tennis', 'handball']:
        if not all_matches.get(sport):
            continue
        
        sport_icon = {'football': '⚽', 'tennis': '🎾', 'handball': '🤾'}[sport]
        print(f"{sport_icon} {sport.upper()}: {len(all_matches[sport])} матчей\n")

        if sport not in enabled_sports:
            print("   ⚠️ Этот вид спорта временно пропускаем (анализ только футбол)\n")
            continue
        
        for match in all_matches[sport]:
            stats['total'] += 1
            
            team1 = match.get('team1') or match.get('player1')
            team2 = match.get('team2') or match.get('player2')
            score = match.get('score', '')
            odds = match.get('odds', '')
            league = match.get('league') or match.get('tournament') or ''
            minute = match.get('time', '') or ''
            
            print(f"   {team1} - {team2}")
            odds_str = f"{odds}" if odds not in (None, '') else "—"
            print(f"   Счет: {score}, Минуты: {minute}, Коэфф: {odds_str}")

            if not is_league_allowed(league, team1, team2):
                if league:
                    print(f"   ❌ Турнир исключен правилами отбора ({league})\n")
                else:
                    print("   ❌ Турнир не определен — пропускаем\n")
                stats['filtered_league'] += 1
                continue
            
            if sport in ['football', 'handball']:
                # ФИЛЬТР 1: Ничья?
                if is_draw(score):
                    print(f"   ❌ НИЧЬЯ - пропускаем\n")
                    stats['filtered_draw'] += 1
                    continue
                print(f"   ✅ ПОДХОДИТ - добавляем для проверки на Scores24\n")
                stats['passed'] += 1
                filtered[sport].append(match)
                candidate_rows.append({
                    'team1': team1,
                    'team2': team2,
                    'score': score,
                    'time': minute,
                    'odds': odds_str,
                    'league': league
                })
            elif sport == 'tennis':
                # ТЕННИС: 1-й сет выигран + ведет во 2-м ИЛИ ведет 3+ в текущем
                try:
                    s = (score or '').strip()
                    passed = False
                    if ',' in s:
                        parts = [p.strip() for p in s.split(',')]
                        if ':' in parts[0]:
                            a1, b1 = parse_score(parts[0])
                            if a1 is not None and a1 > b1:
                                if len(parts) > 1 and ':' in parts[1]:
                                    a2, b2 = parse_score(parts[1])
                                    passed = (a2 is not None and a2 > b2)
                                else:
                                    passed = True
                    else:
                        # Текущий сет (без запятой) и лидерство 3+
                        a, b = parse_score(s)
                        if a is not None and (a - b) >= 3:
                            passed = True
                    if not passed:
                        print(f"   ❌ Не проходит теннисные критерии - пропускаем\n")
                        stats['filtered_other'] += 1
                        continue
                    print(f"   ✅ ПОДХОДИТ (теннисные критерии) - добавляем для проверки на Scores24\n")
                    stats['passed'] += 1
                    filtered[sport].append(match)
                except Exception:
                    print(f"   ❌ Ошибка парсинга теннисного счета - пропускаем\n")
                    stats['filtered_draw'] += 1
                    continue
    
    # Итоги фильтрации
    print("="*70)
    print("📊 ИТОГИ ФИЛЬТРАЦИИ НА BETBOOM")
    print("="*70)
    if candidate_rows:
        print("🗂️ Черновик кандидатов (BetBoom):")
        header = f"{'№':<3} {'Матч':<45} {'Счёт':<8} {'Мин':<7} {'Кэф':<6} Лига"
        print(header)
        print("-" * len(header))
        for idx, row in enumerate(candidate_rows, 1):
            match_caption = f"{row['team1']} vs {row['team2']}"
            print(f"{idx:<3} {match_caption:<45.45} {row['score']:<8} {row['time']:<7} {row['odds']:<6} {row['league']}")
        print("-" * len(header))
    else:
        print("⚠️ После фильтрации кандидатов нет.")
    print(f"Всего матчей: {stats['total']}")
    print(f"Отфильтровано:")
    print(f"  • Ничьи: {stats['filtered_draw']}")
    print(f"  • Турнир не подходит: {stats['filtered_league']}")
    print(f"  • Другие причины: {stats['filtered_other']}")
    print(f"✅ Прошли фильтр: {stats['passed']}")
    print("="*70 + "\n")
    
    stats['candidates'] = candidate_rows
    return filtered, stats

# ===================== ПРОВЕРКА НА SCORES24 =====================

def verify_on_scores24(
    filtered_matches,
    mcp_browser_navigate=None,
    mcp_browser_wait=None,
    mcp_browser_snapshot=None,
    send_callback=None
):
    """
    ШАГ 2: Проверка ТОЛЬКО отфильтрованных матчей на Scores24 через MCP Browser
    
    Args:
        filtered_matches: отфильтрованные матчи
        mcp_browser_navigate: функция MCP Browser для навигации (опционально)
        mcp_browser_wait: функция MCP Browser для ожидания (опционально)
        mcp_browser_snapshot: функция MCP Browser для snapshot (опционально)
    
    ВАЖНО: Если MCP функции не переданы, функция вернет пустой список
    """
    print("="*70)
    print("🔍 ШАГ 2: ПРОВЕРКА НА SCORES24 (MCP BROWSER)")
    print("="*70 + "\n")
    
    if not any(filtered_matches.values()):
        print("⚠️ Нет матчей для проверки после фильтрации\n")
        return []
    
    # Проверяем наличие MCP Browser функций
    if not all([mcp_browser_navigate, mcp_browser_wait, mcp_browser_snapshot]):
        print("⚠️ MCP Browser функции не переданы")
        print("   Проверка через MCP Browser требует контекста Cursor")
        print("   Функция должна вызываться с передачей MCP Browser инструментов\n")
        return []
    
    from scores24_mcp_checker import check_match_on_scores24_mcp

    def build_prepared_payload(match_info, details_text):
        team1 = match_info.get('team1') or match_info.get('player1', '')
        team2 = match_info.get('team2') or match_info.get('player2', '')
        league_name = match_info.get('league') or match_info.get('tournament', '')
        score_str = match_info.get('score', '')
        time_str = match_info.get('time', 'live')
        payload = {
            'title': f"{team1} - {team2}",
            'league': f"   {league_name}",
            'score': f"   Счет: {score_str} ({time_str})",
            'details': f"   📌 {details_text}" if details_text else "",
            'team1': team1,
            'team2': team2,
            'league_name': league_name,
            'score_text': score_str,
            'time_text': time_str
        }
        return payload
    
    verified = []
    
    try:
        total_candidates = sum(len(filtered_matches[s]) for s in ['football', 'tennis', 'handball'])
        print(f"🧾 Кандидатов на проверку: {total_candidates}\n")
        for sport in ['football', 'tennis', 'handball']:
            if not filtered_matches[sport]:
                continue
            
            sport_icon = {'football': '⚽', 'tennis': '🎾', 'handball': '🤾'}[sport]
            print(f"{sport_icon} {sport.upper()}: {len(filtered_matches[sport])} матчей\n")
            
            live_snapshot_text = None
            urls = {
                'football': 'https://scores24.live/ru/soccer?matchesFilter=live',
                'tennis': 'https://scores24.live/ru/tennis?matchesFilter=live',
                'handball': 'https://scores24.live/ru/handball?matchesFilter=live'
            }
            
            try:
                list_url = urls[sport]
                print(f"   📡 Загружаю live-список: {list_url}")
                mcp_browser_navigate(list_url)
                mcp_browser_wait(time=5)
                snapshot_result = mcp_browser_snapshot()
                live_snapshot_text = snapshot_result.get('snapshot', '') if isinstance(snapshot_result, dict) else str(snapshot_result)
            except Exception as e:
                print(f"   ⚠️ Не удалось получить live-список: {e}")
                live_snapshot_text = None
            
            for i, match in enumerate(filtered_matches[sport], 1):
                team1 = match.get('team1') or match.get('player1')
                team2 = match.get('team2') or match.get('player2')
                
                print(f"[{i}/{len(filtered_matches[sport])}]")
                
                result = check_match_on_scores24_mcp(
                    sport, team1, team2, match,
                    mcp_browser_navigate,
                    mcp_browser_wait,
                    mcp_browser_snapshot,
                    live_snapshot_text=live_snapshot_text
                )
                
                if result.get('verified'):
                    prepared_payload = build_prepared_payload(match, result.get('details', ''))
                    result['prebuilt_payload'] = prepared_payload
                    verified.append((sport, result))
                    print(f"✅ ПОДТВЕРЖДЕН на Scores24")
                    print(f"   🧩 Блок для сообщения готов\n")
                    if send_callback:
                        send_callback([(sport, result)])
                else:
                    reason = result.get('reason')
                    if reason == 'no_stats':
                        print("❌ На Scores24 нет live-статистики — пропускаем\n")
                    elif reason == 'error_collecting_stats':
                        print(f"❌ Не удалось собрать статистику: {result.get('error')}\n")
                    else:
                        print(f"❌ Не найден на Scores24\n")
    
    except Exception as e:
        print(f"❌ Ошибка при проверке: {e}\n")
        import traceback
        traceback.print_exc()
    
    print("="*70)
    print("📊 ИТОГИ ПРОВЕРКИ")
    print("="*70)
    print(f"Проверено матчей: {sum(len(filtered_matches[s]) for s in ['football', 'tennis', 'handball'])}")
    print(f"Найдено на Scores24: {len(verified)}")
    print("="*70 + "\n")
    
    return verified

# ===================== СОХРАНЕНИЕ В ML ФАЙЛЫ =====================

def save_to_ml(verified_matches):
    """
    ШАГ 4: Сохранение данных в ML файлы для обучения
    Вызывается ПОСЛЕ отправки в Telegram
    """
    try:
        logger = PredictionLoggerML()
        saved_count = 0
        
        for sport, data in verified_matches:
            match = data.get('match', {})
            stats = data.get('stats', {})
            
            # Определяем категорию по коэффициенту
            odds = match.get('odds', 999)
            if odds <= 1.05:
                category = 'dead'
            elif odds <= 1.20:
                category = 'perfect'
            elif odds <= 1.50:
                category = 'good'
            else:
                category = 'acceptable'
            
            # Формируем данные матча
            match_data = {
                'sport': sport,
                'team1': match.get('team1') or match.get('player1', ''),
                'team2': match.get('team2') or match.get('player2', ''),
                'league': match.get('league') or match.get('tournament', ''),
                'score': match.get('score', ''),
                'time': match.get('time', ''),
                'odds': odds,
                'category': category
            }
            
            # Формируем статистику Scores24
            scores24_stats = {
                'match_stats': stats.get('match_stats', {}),
                'h2h': stats.get('h2h'),
                'form': stats.get('form')
            }
            
            # Сохраняем в ML файл
            pred_id = logger.add_prediction_ml(match_data, scores24_stats)
            saved_count += 1
            print(f"   ✅ Сохранен матч #{pred_id}: {match_data['team1']} - {match_data['team2']}")
        
        print(f"\n📊 Всего сохранено в ML: {saved_count} матчей")
        print(f"📁 Файл: predictions_ml_log.json")
        
    except Exception as e:
        print(f"⚠️ Ошибка при сохранении в ML: {e}")
        import traceback
        traceback.print_exc()

# ===================== ПРОВЕРКА РЕЗУЛЬТАТОВ =====================

def check_old_results(mcp_browser_navigate=None, mcp_browser_wait=None, mcp_browser_snapshot=None):
    """
    ШАГ 5: Проверка результатов старых прогнозов
    Проверяет pending прогнозы старше 90 минут
    """
    if not all([mcp_browser_navigate, mcp_browser_wait, mcp_browser_snapshot]):
        print("⚠️ MCP Browser функции не доступны - проверка результатов пропущена")
        return
    
    try:
        stats = check_pending_results_mcp(
            min_age_minutes=90,  # Проверяем прогнозы старше 90 минут
            mcp_browser_navigate=mcp_browser_navigate,
            mcp_browser_wait=mcp_browser_wait,
            mcp_browser_snapshot=mcp_browser_snapshot
        )
        
        if stats['updated'] > 0:
            print(f"\n✅ Обновлено результатов: {stats['updated']}")
    except Exception as e:
        print(f"⚠️ Ошибка при проверке результатов: {e}")

# ===================== ОТПРАВКА В TELEGRAM =====================

def save_backup_message(message_text: str):
    """Сохраняет сообщение в резерв, если Telegram недоступен."""
    try:
        backup_dir = Path('telegram_failed_messages')
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = backup_dir / f"message_{timestamp}.txt"
        backup_file.write_text(message_text, encoding='utf-8')
        print(f"   💾 Резервная копия сохранена: {backup_file}")
    except Exception as err:
        print(f"   ⚠️ Не удалось сохранить резервную копию: {err}")


def send_results(verified_matches, filter_stats, error_message=None):
    """ШАГ 3: Отправка результатов."""
    
    # КРИТИЧЕСКАЯ ПРОВЕРКА: НЕ ОТПРАВЛЯЕМ НИЧЕЙНЫЕ МАТЧИ!
    if verified_matches:
        filtered_verified = []
        for match in verified_matches:
            score = match.get('score', '')
            if is_draw(score):
                print(f"🚨 КРИТИЧЕСКАЯ ОШИБКА: Попытка отправить ничейный матч {match.get('team1', '')} vs {match.get('team2', '')} ({score}) - БЛОКИРУЕМ!")
                continue
            filtered_verified.append(match)
        verified_matches = filtered_verified
        
        if not verified_matches:
            print("🚨 ВСЕ МАТЧИ БЫЛИ НИЧЕЙНЫМИ - ОТПРАВЛЯЕМ СООБЩЕНИЕ ОБ ОТСУТСТВИИ ПОДХОДЯЩИХ МАТЧЕЙ")
    
    current_time = datetime.now().strftime('%H:%M')
    current_date = datetime.now().strftime('%d.%m.%Y')

    if not filter_stats:
        filter_stats = {
            'total': 0,
            'filtered_draw': 0,
            'filtered_league': 0,
            'filtered_other': 0,
            'passed': 0,
            'candidates': []
        }

    def format_odds(odds_value):
        if isinstance(odds_value, (int, float)):
            return f"~{odds_value:.2f}"
        if isinstance(odds_value, str) and odds_value.strip():
            return odds_value if odds_value.strip().startswith("~") else f"~{odds_value}"
        return "~1.00"

    def determine_recommendation(match_dict, score_tuple):
        custom = match_dict.get('recommendation')
        if custom:
            return custom
        if score_tuple and score_tuple[0] is not None and score_tuple[1] is not None:
            if score_tuple[0] > score_tuple[1]:
                return "П1"
            if score_tuple[1] > score_tuple[0]:
                return "П2"
        return "Победа фаворита"

    def category_by_odds(odds_value):
        if not isinstance(odds_value, (int, float)):
            return "✅ ИДЕАЛЬНЫЙ ⭐⭐⭐⭐"
        if odds_value <= 1.05:
            return "✅ МЕРТВЫЙ ⭐⭐⭐⭐⭐"
        if odds_value <= 1.20:
            return "✅ ИДЕАЛЬНЫЙ ⭐⭐⭐⭐"
        if odds_value <= 1.40:
            return "✅ ОТЛИЧНЫЙ ⭐⭐⭐"
        return "✅ ХОРОШИЙ ⭐⭐"

    def make_match_blocks(matches):
        blocks = []
        for idx, data in enumerate(matches, 1):
            match_info = data['match']
            prebuilt = data.get('prebuilt_payload') or {}

            team1 = prebuilt.get('team1') or match_info.get('team1') or match_info.get('player1', '')
            team2 = prebuilt.get('team2') or match_info.get('team2') or match_info.get('player2', '')
            league_name = prebuilt.get('league_name') or match_info.get('league') or match_info.get('tournament', '')
            score_str = prebuilt.get('score_text') or match_info.get('score', '')
            time_str = prebuilt.get('time_text') or match_info.get('time', 'live')
            score_tuple = parse_score(score_str)
            recommendation = determine_recommendation(match_info, score_tuple)
            odds_value = match_info.get('odds')
            odds_formatted = format_odds(odds_value)
            details_text = data.get('details') or prebuilt.get('details', '').strip()
            if details_text and not details_text.startswith("📌"):
                details_text = f"📌 {details_text}"
            elif not details_text:
                details_text = "📌 Контроль подтверждён статистикой."
            category_label = match_info.get('category_label') or category_by_odds(odds_value)

            block_lines = [
                f"{idx}️⃣ {team1} - {team2}",
                f"   {league_name}",
                f"   Счет: {score_str} ({time_str})",
                f"   Рекомендация: {recommendation} - коэф. {odds_formatted}",
                "",
                f"   {details_text}",
                f"   {category_label}",
            ]

            blocks.append("\n".join(line for line in block_lines if line))
        return "\n\n".join(blocks)

    if error_message:
        message = f"""───────────────────────────────────
📊 АНАЛИЗ LIVE-МАТЧЕЙ НА {current_time} МСК ({current_date})

⚠️ ОШИБКА ПРИ АНАЛИЗЕ

{error_message}

---
⏰ {current_time} МСК
🤖 TrueLiveBet | Честные прогнозы с ИИ
───────────────────────────────────"""
    elif not verified_matches:
        disclaimer_text = get_next_disclaimer()
        message = f"""🎯 LIVE-АНАЛИЗ • {current_time} МСК, {current_date}

—————————————

⚽ ФУТБОЛ ⚽

—————————————

В данный момент подходящих матчей для рекомендации не найдено.

Следующий анализ через 45 минут.

—————————————

🔥 @TrueLiveBet | Честные прогнозы с ИИ

{disclaimer_text}"""
    else:
        disclaimer_text = get_next_disclaimer()

        by_sport = {'football': [], 'tennis': [], 'handball': []}
        for sport, data in verified_matches:
            by_sport[sport].append(data)

        sections = ["🎯 LIVE-АНАЛИЗ • {0} МСК, {1}".format(current_time, current_date), "", "—————————————", ""]

        if by_sport['football']:
            sections.extend([
                "⚽ ФУТБОЛ ⚽",
                "",
                "—————————————",
                "",
                make_match_blocks(by_sport['football'])
            ])

        if by_sport['tennis']:
            sections.extend([
                "",
                "🎾 ТЕННИС 🎾",
                "",
                "—————————————",
                "",
                make_match_blocks(by_sport['tennis'])
            ])

        if by_sport['handball']:
            sections.extend([
                "",
                "🤾 ГАНДБОЛ 🤾",
                "",
                "—————————————",
                "",
                make_match_blocks(by_sport['handball'])
            ])

        sections.extend([
            "",
            "—————————————",
            "",
            "🔥 @TrueLiveBet | Честные прогнозы с ИИ",
            "",
            disclaimer_text
        ])

        message = "\n".join(section for section in sections)

    try:
        with open('current_live_analysis_mcp.txt', 'w', encoding='utf-8') as f:
            f.write(message)
        print("✅ Сообщение сохранено в current_live_analysis_mcp.txt\n")
    except Exception as e:
        print(f"⚠️ Ошибка сохранения в файл: {e}\n")

    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    payload = {'chat_id': CHANNEL, 'text': message}

    os.environ.pop("REQUESTS_CA_BUNDLE", None)
    os.environ.pop("CURL_CA_BUNDLE", None)

    session = requests.Session()
    session.verify = False
    session.headers.update({
        "Connection": "close",
        "User-Agent": "TrueLiveBet-Autobot/1.0"
    })

    print("📨 Старт отправки в Telegram (до 5 попыток)...")
    for attempt in range(1, 6):
        try:
            response = session.post(url, json=payload, timeout=30)
            if response.ok:
                print(f"✅ Отправлено в {CHANNEL} (попытка {attempt})\n")
                break
            print(f"⚠️ Telegram ответил ошибкой (попытка {attempt}): {response.text}\n")
        except Exception as exc:
            print(f"⚠️ Ошибка при отправке (попытка {attempt}): {exc}\n")
        sleep_delay = min(3 * attempt, 10)
        print(f"   ⏳ Пауза перед повтором: {sleep_delay} сек.")
        time.sleep(sleep_delay)
    else:
        print("❌ Telegram не принял сообщение после 5 попыток. Сохраняю резервную копию.\n")
        save_backup_message(message)

# ===================== ГЛАВНАЯ ФУНКЦИЯ =====================

def main(mcp_browser_navigate=None, mcp_browser_wait=None, mcp_browser_snapshot=None):
    """
    ПРАВИЛЬНЫЙ АЛГОРИТМ:
    1. BetBoom → все матчи
    2. Фильтр на BetBoom → только неничейные + допустимые турниры
    3. Scores24 → проверить ТОЛЬКО отфильтрованные (через MCP Browser)
    4. Telegram → отправить
    
    Args:
        mcp_browser_navigate: функция MCP Browser для навигации (опционально)
        mcp_browser_wait: функция MCP Browser для ожидания (опционально)
        mcp_browser_snapshot: функция MCP Browser для snapshot (опционально)
    
    ВАЖНО: Для проверки Scores24 через MCP Browser нужно передать MCP функции
    """
    print("\n" + "="*70)
    print("АНАЛИЗ ЛАЙВ-МАТЧЕЙ С ПРЕФИЛЬТРОМ")
    print("="*70 + "\n")
    
    # КРИТИЧНО: Проверяем наличие MCP Browser функций ПЕРЕД началом анализа
    if not all([mcp_browser_navigate, mcp_browser_wait, mcp_browser_snapshot]):
        print("WARNING: MCP Browser функции не доступны!")
        print("   Скрипт запущен вне контекста Cursor (например, из AHK)")
        print("   Без проверки на Scores24 нельзя дать достоверную информацию")
        print("   Сообщение в Telegram НЕ будет отправлено\n")
        print("="*70)
        print("ANALYSIS STOPPED: требуется контекст Cursor с MCP Browser")
        print("="*70 + "\n")
        return  # Выходим БЕЗ отправки сообщения
    
    # Инициализируем переменные для обработки ошибок
    verified = []
    filter_stats = {
        'total': 0,
        'filtered_draw': 0,
        'filtered_league': 0,
        'filtered_other': 0,
        'passed': 0,
        'candidates': []
    }
    error_msg = None
    sent_chunks = 0

    def immediate_send(chunk):
        nonlocal sent_chunks
        sent_chunks += 1
        send_results(chunk, filter_stats)
    
    try:
        # Получаем матчи через MCP-коннектор BetBoom (без selenium)
        all_matches = get_betboom_matches_mcp()
        
        # ШАГ 1: Фильтрация на BetBoom
        filtered, filter_stats = prefilter_betboom_matches(all_matches)
        
        # ШАГ 2: Проверка на Scores24 ТОЛЬКО отфильтрованных (через MCP Browser)
        verified = verify_on_scores24(
            filtered,
            mcp_browser_navigate=mcp_browser_navigate,
            mcp_browser_wait=mcp_browser_wait,
            mcp_browser_snapshot=mcp_browser_snapshot,
            send_callback=immediate_send
        )
    except Exception as e:
        error_msg = f"Ошибка при анализе матчей: {str(e)}"
        print(f"❌ {error_msg}\n")
        import traceback
        traceback.print_exc()
        # Продолжаем выполнение, чтобы отправить сообщение об ошибке
    
    # ШАГ 3: Отправка (только если была проверка на Scores24)
    print("="*70)
    print("📤 ШАГ 3: ОТПРАВКА В TELEGRAM")
    print("="*70 + "\n")
    if error_msg:
        send_results([], filter_stats, error_message=error_msg)
    elif sent_chunks == 0:
        # Даже если матчей нет – обязательно отправляем статус
        send_results(verified, filter_stats, error_message=None)
    
    # ШАГ 4: Сохранение в ML файлы
    if verified:
        print("="*70)
        print("💾 ШАГ 4: СОХРАНЕНИЕ В ML ФАЙЛЫ")
        print("="*70 + "\n")
        save_to_ml(verified)
        
        # ШАГ 5: Проверка старых результатов (если есть pending)
        print("="*70)
        print("🔍 ШАГ 5: ПРОВЕРКА РЕЗУЛЬТАТОВ СТАРЫХ ПРОГНОЗОВ")
        print("="*70 + "\n")
        check_old_results(mcp_browser_navigate, mcp_browser_wait, mcp_browser_snapshot)
    
    print("\n✅ АНАЛИЗ ЗАВЕРШЕН!\n")

if __name__ == "__main__":
    main()

