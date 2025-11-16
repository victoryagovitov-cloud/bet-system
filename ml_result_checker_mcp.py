# -*- coding: utf-8 -*-
"""
💾 ML-РЕЗУЛЬТАТЫ: Проверка финальных счетов через MCP Browser
Обновляет статусы прогнозов в predictions_ml_log.json
"""
from datetime import datetime
from prediction_logger_ml import PredictionLoggerML
from scores24_mcp_connector import get_name_variants


def check_match_result_mcp(sport, team1, team2, mcp_browser_navigate, mcp_browser_wait, mcp_browser_snapshot):
    """
    Проверяет финальный результат матча на Scores24 через MCP Browser
    
    Args:
        sport: 'football', 'tennis', 'handball'
        team1: название первой команды/игрока
        team2: название второй команды/игрока
        mcp_browser_navigate: функция MCP Browser для навигации
        mcp_browser_wait: функция MCP Browser для ожидания
        mcp_browser_snapshot: функция MCP Browser для получения snapshot
    
    Returns:
        dict: {'status': 'won'/'lost'/'pending'/'cancelled', 'final_score': '3:0'}
    """
    urls = {
        'football': 'https://scores24.live/ru/soccer?matchesFilter=finished',
        'tennis': 'https://scores24.live/ru/tennis?matchesFilter=finished',
        'handball': 'https://scores24.live/ru/handball?matchesFilter=finished'
    }
    
    if sport not in urls:
        return {'status': 'cancelled', 'final_score': None}
    
    try:
        # Открываем страницу завершенных матчей
        url = urls[sport]
        print(f"   📡 Открываю: {url}")
        mcp_browser_navigate(url)
        mcp_browser_wait(time=5)
        
        # Получаем snapshot
        snapshot_result = mcp_browser_snapshot()
        snapshot_text = snapshot_result.get('snapshot', '') if isinstance(snapshot_result, dict) else str(snapshot_result)
        
        # Генерируем варианты названий
        team1_variants = get_name_variants(team1)
        team2_variants = get_name_variants(team2)
        
        # Проверяем наличие матча
        snapshot_lower = snapshot_text.lower()
        team1_found = any(v.lower() in snapshot_lower for v in team1_variants[:5])
        team2_found = any(v.lower() in snapshot_lower for v in team2_variants[:5])
        
        if not (team1_found and team2_found):
            print(f"   ⏳ Матч еще не завершился или не найден")
            return {'status': 'pending', 'final_score': None}
        
        # Ищем финальный счет в snapshot
        import re
        
        # Для футбола и гандбола: ищем паттерн "число:число"
        if sport in ['football', 'handball']:
            # УЛУЧШЕНИЕ: Ищем счет в контексте найденных команд
            # Разбиваем snapshot на строки для более точного поиска
            lines = snapshot_text.split('\n')
            
            # Ищем строки, где есть обе команды
            match_lines = []
            for i, line in enumerate(lines):
                line_lower = line.lower()
                has_team1 = any(v.lower() in line_lower for v in team1_variants[:5])
                has_team2 = any(v.lower() in line_lower for v in team2_variants[:5])
                
                if has_team1 or has_team2:
                    # Берем эту строку и соседние (для контекста)
                    start = max(0, i - 2)
                    end = min(len(lines), i + 3)
                    context = '\n'.join(lines[start:end])
                    match_lines.append(context)
            
            # Ищем счет в контексте матча
            score_pattern = r'(\d+)\s*[:]\s*(\d+)'
            final_score = None
            
            # Сначала ищем в контексте матча
            for match_context in match_lines:
                scores = re.findall(score_pattern, match_context)
                if scores:
                    # Проверяем, что это похоже на финальный счет (не время, не дата)
                    for score_match in scores:
                        score1_val = int(score_match[0])
                        score2_val = int(score_match[1])
                        # Валидация: счет должен быть разумным (не 99:99, не 0:0 для завершенного)
                        if 0 <= score1_val <= 20 and 0 <= score2_val <= 20:
                            final_score = f"{score_match[0]}:{score_match[1]}"
                            break
                    if final_score:
                        break
            
            # Если не нашли в контексте, ищем по всей странице (fallback)
            if not final_score:
                all_scores = re.findall(score_pattern, snapshot_text)
                if all_scores:
                    # Берем первый разумный счет
                    for score_match in all_scores:
                        score1_val = int(score_match[0])
                        score2_val = int(score_match[1])
                        if 0 <= score1_val <= 20 and 0 <= score2_val <= 20:
                            final_score = f"{score_match[0]}:{score_match[1]}"
                            break
            
            if final_score:
                parts = final_score.split(':')
                score1, score2 = int(parts[0]), int(parts[1])
                
                print(f"   📊 Финальный счет: {final_score}")
                
                # Определяем результат
                if score1 > score2:
                    return {'status': 'won', 'final_score': final_score}
                elif score1 < score2:
                    return {'status': 'lost', 'final_score': final_score}
                else:
                    return {'status': 'cancelled', 'final_score': final_score}  # Ничья
        
        # Для тенниса: ищем счет по сетам
        elif sport == 'tennis':
            # Ищем паттерн типа "6:4 6:2" или "2:0" (по сетам)
            set_pattern = r'(\d+)\s*[:]\s*(\d+)'
            sets = re.findall(set_pattern, snapshot_text)
            
            if len(sets) >= 2:
                # Считаем выигранные сеты
                sets_won_1 = 0
                sets_won_2 = 0
                
                for set_score in sets[:3]:  # Максимум 3 сета
                    if int(set_score[0]) > int(set_score[1]):
                        sets_won_1 += 1
                    elif int(set_score[0]) < int(set_score[1]):
                        sets_won_2 += 1
                
                # Формируем финальный счет по сетам
                final_score = f"{sets_won_1}:{sets_won_2}"
                
                print(f"   📊 Финальный счет по сетам: {final_score}")
                
                if sets_won_1 > sets_won_2:
                    return {'status': 'won', 'final_score': final_score}
                elif sets_won_1 < sets_won_2:
                    return {'status': 'lost', 'final_score': final_score}
        
        print(f"   ⚠️ Не удалось определить финальный счет")
        return {'status': 'pending', 'final_score': None}
        
    except Exception as e:
        print(f"   ❌ Ошибка при проверке результата: {e}")
        import traceback
        traceback.print_exc()
        return {'status': 'pending', 'final_score': None}


def check_pending_results_mcp(min_age_minutes=90, mcp_browser_navigate=None, mcp_browser_wait=None, mcp_browser_snapshot=None, prediction_id=None):
    """
    Проверяет результаты всех pending прогнозов через MCP Browser
    
    Args:
        min_age_minutes: минимальный возраст прогноза для проверки (по умолчанию 90 минут)
        mcp_browser_navigate: функция MCP Browser для навигации
        mcp_browser_wait: функция MCP Browser для ожидания
        mcp_browser_snapshot: функция MCP Browser для получения snapshot
    
    Returns:
        dict: статистика проверки
    """
    if not all([mcp_browser_navigate, mcp_browser_wait, mcp_browser_snapshot]):
        print("⚠️ MCP Browser функции не переданы - проверка результатов пропущена")
        return {'checked': 0, 'updated': 0, 'errors': 0}
    
    ml = PredictionLoggerML()
    
    # Получаем все pending прогнозы
    pending = [p for p in ml.predictions['predictions'] if p.get('status') == 'pending']
    
    if not pending:
        print("✅ Нет прогнозов в статусе pending")
        return {'checked': 0, 'updated': 0, 'errors': 0}
    
    print(f"\n📋 Найдено pending прогнозов: {len(pending)}")
    print(f"⏱ Минимальный возраст для проверки: {min_age_minutes} минут\n")
    
    checked = 0
    updated = 0
    errors = 0
    
    for pred in pending:
        try:
            # Проверяем возраст прогноза
            try:
                ts = datetime.fromisoformat(pred['timestamp'])
            except Exception:
                ts = datetime.now()
            
            age_minutes = (datetime.now() - ts).total_seconds() / 60
            
            if age_minutes < min_age_minutes:
                continue
            
            checked += 1
            
            print(f"\n🔍 Проверяю прогноз #{pred['id']}:")
            print(f"   {pred['team1']} - {pred['team2']}")
            print(f"   Возраст: {int(age_minutes)} минут")
            print(f"   Прогноз: П1 {pred.get('team1', '')} (коэф. {pred.get('odds', 'N/A')})")
            
            # Проверяем результат
            result = check_match_result_mcp(
                pred['sport'],
                pred['team1'],
                pred['team2'],
                mcp_browser_navigate,
                mcp_browser_wait,
                mcp_browser_snapshot
            )
            
            if result.get('status') in ('won', 'lost', 'cancelled') and result.get('final_score'):
                # Определяем правильный статус с учетом рекомендации (П1 или П2)
                recommendation = pred.get('recommendation', 'П1')
                
                # Если ставили на П2, нужно инвертировать результат
                if recommendation == 'П2':
                    if result['status'] == 'won':
                        result['status'] = 'lost'
                    elif result['status'] == 'lost':
                        result['status'] = 'won'
                
                # Обновляем прогноз
                ml.update_prediction_result_ml(
                    pred['id'],
                    result['final_score'],
                    result['status']
                )
                updated += 1
                print(f"   ✅ Обновлен: {result['status']} ({result['final_score']})")
            else:
                print(f"   ⏳ Результат еще не доступен")
                
        except Exception as e:
            errors += 1
            print(f"   ❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n📊 ИТОГИ ПРОВЕРКИ:")
    print(f"   Проверено: {checked}")
    print(f"   Обновлено: {updated}")
    print(f"   Ошибок: {errors}")
    
    return {'checked': checked, 'updated': updated, 'errors': errors}


if __name__ == "__main__":
    # Для автономного запуска нужны MCP функции
    # В реальном использовании они передаются из Cursor
    print("⚠️ Этот скрипт должен запускаться из Cursor с MCP Browser функциями")
    print("Используйте: check_pending_results_mcp(mcp_browser_navigate, mcp_browser_wait, mcp_browser_snapshot)")

