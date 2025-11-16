# -*- coding: utf-8 -*-
"""
ПАКЕТНАЯ ОТПРАВКА АНАЛИЗА (по 4 матча) С ПАРАЛЛЕЛЬНОЙ ПРОВЕРКОЙ SCORES24

Правила:
- Префильтр дает список кандидатов
- Проверка на Scores24 идет параллельно
- Как только готово 4 матча — формируем сообщение и отправляем в Telegram
- Продолжаем до исчерпания очереди
- Данные в ML записываются ПОСЛЕ того как все сообщения отправлены
- Опубликованные прогнозы сохраняются в published_predictions.json для последующей проверки результатов
"""

import sys
import io
import json
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple

import requests
import subprocess

from prediction_logger_ml import PredictionLoggerML
from improved_scores24_connector import setup_driver_improved, check_scores24_improved

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


TELEGRAM_CONFIG = None
with open('config.json', 'r', encoding='utf-8') as f:
    TELEGRAM_CONFIG = json.load(f)['notifications']['telegram']


def send_telegram_message(text: str) -> Dict:
    """Сохраняем текст в current_live_analysis_mcp.txt и вызываем send_fixed_analysis.py
    чтобы сохранить прежний транспорт и форматирование сообщений."""
    try:
        with open('current_live_analysis_mcp.txt', 'w', encoding='utf-8') as f:
            f.write(text)
    except Exception as e:
        return {"ok": False, "error": f"write_file: {e}"}

    try:
        result = subprocess.run(['python', 'send_fixed_analysis.py'], capture_output=True, text=True, encoding='utf-8')
        # Скрипт сам печатает результат; для унификации вернём ok по коду возврата
        return {"ok": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr}
    except Exception as e:
        return {"ok": False, "error": f"subprocess: {e}"}


def format_batch_message(batch_idx: int, total_batches: int, items: List[Dict]) -> str:
    now = datetime.now().strftime('%H:%M')
    parts = [
        f"🧠 ИИ-АНАЛИЗ LIVE • {now} МСК",
        "",
        "-" * 45,
        f"📦 Пакет {batch_idx}/{total_batches}",
        "",
    ]
    for i, it in enumerate(items, 1):
        m = it['match']
        parts += [
            f"{i}. ⚽ {m['team1']} - {m['team2']}",
            f"🏟️ {m.get('league', '')}",
            f"📊 Счет: {m['score']} ({m['time']})",
            f"✅ Ставка: П1 {m.get('team1')} | коэф. ~{m.get('odds')}",
            "",
            "📈 РЕАЛЬНАЯ СТАТИСТИКА (Scores24):",
            f"• xG: {it['stats'].get('xg', '—')}",
            f"• Владение: {it['stats'].get('possession', '—')}",
            f"• Удары: {it['stats'].get('shots', '—')}",
            f"• Удары в створ: {it['stats'].get('shots_on_target', '—')}",
            f"• Угловые: {it['stats'].get('corners', '—')}",
            "",
            "🎯 АНАЛИЗ:",
            it.get('analysis', 'Фаворит ведет и подтвержден по статистике.'),
            f"⚡ ВЕРОЯТНОСТЬ: ~{it.get('probability', 85)}%",
            "",
            "-" * 45,
            "",
        ]
    parts += [
        f"⏰ {now} МСК",
        "🤖 TrueLiveBet | Точные прогнозы",
        "",
        "Напоминание: ставки — это риск. Наш анализ не финансовый совет.",
    ]
    return "\n".join(parts)


def to_ml_payload(item: Dict) -> Tuple[Dict, Dict]:
    m = item['match']
    stats = item['stats_full']  # полный словарь для ML
    match_data = {
        'sport': m.get('sport', 'football'),
        'team1': m['team1'],
        'team2': m['team2'],
        'league': m.get('league', ''),
        'score': m['score'],
        'time': m['time'],
        'odds': float(m.get('odds', 1.01)),
        'category': item.get('category', 'good'),
    }
    return match_data, stats


def verify_match(driver, sport: str, match: Dict) -> Dict:
    team1 = match.get('team1') or match.get('player1')
    team2 = match.get('team2') or match.get('player2')
    res = check_scores24_improved(driver, sport, team1, team2, match)
    if not res.get('verified'):
        return {"verified": False}
    # Нормализуем краткую статистику для сообщения
    s = res.get('stats', {})
    brief = {
        'xg': s.get('xg_str') or s.get('xg') or '—',
        'possession': s.get('possession_str') or s.get('possession') or '—',
        'shots': s.get('shots') or '—',
        'shots_on_target': s.get('shots_on_target') or '—',
        'corners': s.get('corners') or '—',
    }
    return {
        'verified': True,
        'match': match,
        'stats': brief,
        'stats_full': res.get('stats', {}),
        'analysis': res.get('details', 'Фаворит подтвержден по метрикам.'),
        'probability': res.get('probability', 85),
        'category': res.get('category', 'good'),
    }


def run_batch_pipeline(all_matches: Dict, batch_size: int = 4) -> None:
    # Локальный бесшумный префильтр (без print)
    def _parse_score(sc: str):
        try:
            a, b = sc.split(':')
            return int(a.strip()), int(b.strip().split()[0])
        except Exception:
            return None, None

    def _prefilter_football(m):
        s1, s2 = _parse_score(m.get('score', ''))
        odds = float(m.get('odds', 999))
        if s1 is None:
            return False
        if s1 == s2:
            return False
        if odds > 2.5:
            return False
        return s1 > s2

    def _prefilter_handball(m):
        return _prefilter_football(m)

    def _prefilter_tennis(m):
        odds = float(m.get('odds', 999))
        if odds > 2.5:
            return False
        score = m.get('score', '')
        # Простое правило: есть запятая (значит сет завершен) или ведет с разницей >=3 в текущем
        if ',' in score:
            parts = [p.strip() for p in score.split(',')]
            if ':' in parts[0]:
                a, b = _parse_score(parts[0])
                if a is not None and a > b:
                    # если есть второй сет и лидерство в нем
                    if len(parts) > 1 and ':' in parts[1]:
                        c, d = _parse_score(parts[1])
                        return c is not None and c > d
                    return True
        # Текущий сет 1-й с отрывом 3+
        if ':' in score and ',' not in score:
            a, b = _parse_score(score)
            if a is not None and (a - b) >= 3:
                return True
        return False

    filtered = {'football': [], 'tennis': [], 'handball': []}
    for sport in ['football', 'tennis', 'handball']:
        for m in (all_matches.get(sport) or []):
            keep = False
            if sport == 'football':
                keep = _prefilter_football(m)
            elif sport == 'handball':
                keep = _prefilter_handball(m)
            elif sport == 'tennis':
                keep = _prefilter_tennis(m)
            if keep:
                filtered[sport].append(m)

    # Собираем общую плоскую очередь по видам спорта
    queue: List[Tuple[str, Dict]] = []
    for sport in ['football', 'tennis', 'handball']:
        for m in filtered.get(sport, []) or []:
            m['sport'] = sport
            queue.append((sport, m))

    if not queue:
        print("⚠️ После префильтра нет матчей для проверки")
        return

    # Переопределяем print для сторонних модулей, у которых могут быть проблемы с stdout
    try:
        import builtins as _builtins, sys as _sys
        def _safe_print(*args, **kwargs):
            try:
                end = kwargs.get('end', '\n')
                stream = getattr(_sys, '__stdout__', None) or _sys.stdout
                stream.write(' '.join(str(a) for a in args) + end)
                try:
                    stream.flush()
                except Exception:
                    pass
            except Exception:
                try:
                    # Последний резерв — оригинальный print
                    _builtins.__dict__.get('print', None) and _builtins.print(*args, **kwargs)
                except Exception:
                    pass
        _builtins.print = _safe_print
    except Exception:
        pass

    driver = setup_driver_improved()
    verified_items: List[Dict] = []

    try:
        with ThreadPoolExecutor(max_workers=min(8, max(2, len(queue)))) as pool:
            future_map = {pool.submit(verify_match, driver, sport, m): (sport, m) for sport, m in queue}

            batch_idx = 0
            total_expected_batches = (len(queue) + batch_size - 1) // batch_size
            current_batch: List[Dict] = []

            for fut in as_completed(future_map):
                result = fut.result()
                if not result.get('verified'):
                    continue
                verified_items.append(result)
                current_batch.append(result)

                if len(current_batch) == batch_size:
                    batch_idx += 1
                    text = format_batch_message(batch_idx, total_expected_batches, current_batch)
                    api_res = send_telegram_message(text)
                    if api_res.get('ok'):
                        print(f"✅ Пакет {batch_idx}/{total_expected_batches} отправлен.")
                    else:
                        print(f"❌ Ошибка отправки пакета {batch_idx}: {api_res}")
                    # Сохраним опубликованные прогнозы (минимум данных) для последующей проверки
                    save_published_batch(current_batch, api_res)
                    current_batch = []

            # Хвостовой неполный пакет
            if current_batch:
                batch_idx += 1
                text = format_batch_message(batch_idx, total_expected_batches, current_batch)
                api_res = send_telegram_message(text)
                if api_res.get('ok'):
                    print(f"✅ Пакет {batch_idx}/{total_expected_batches} отправлен.")
                else:
                    print(f"❌ Ошибка отправки пакета {batch_idx}: {api_res}")
                save_published_batch(current_batch, api_res)

    finally:
        try:
            driver.quit()
        except Exception:
            pass

    # ПОСЛЕ того как все сообщения отправлены — сохраняем в ML
    logger = PredictionLoggerML()
    for item in verified_items:
        match_data, stats = to_ml_payload(item)
        logger.add_prediction_ml(match_data, stats)
    print(f"💾 В ML добавлено: {len(verified_items)} записей")


def save_published_batch(batch_items: List[Dict], api_response: Dict) -> None:
    """Сохраняет минимальные данные об опубликованных прогнозах для последующей проверки результатов."""
    record = {
        'timestamp': datetime.now().isoformat(),
        'message_id': (api_response.get('result') or {}).get('message_id') if api_response.get('ok') else None,
        'count': len(batch_items),
        'items': [
            {
                'sport': it['match'].get('sport', 'football'),
                'team1': it['match']['team1'],
                'team2': it['match']['team2'],
                'league': it['match'].get('league', ''),
                'score': it['match']['score'],
                'time': it['match']['time'],
                'odds': it['match'].get('odds'),
            }
            for it in batch_items
        ],
    }
    try:
        path = 'published_predictions.json'
        data = []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            data = []
        data.append(record)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Не удалось сохранить очередь опубликованных прогнозов: {e}")


if __name__ == "__main__":
    # В продакшене сюда подается список матчей после получения с BetBoom (MCP/Selenium)
    # Ниже пример структуры для футболa (заглушка)
    all_matches = {
        'football': [],
        'tennis': [],
        'handball': [],
    }
    run_batch_pipeline(all_matches, batch_size=4)


