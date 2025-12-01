#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Унифицированный модуль для анализа матчей через GPT.
Использует GPT через AITunnel как основной, локальный анализатор только как крайний fallback.
Claude отключен - не используется.
"""

import os
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Новые модули системы
try:
    from system_logger import get_logger, log_info, log_warning, log_error, log_debug
    SYSTEM_LOGGING_AVAILABLE = True
except ImportError:
    SYSTEM_LOGGING_AVAILABLE = False
    # Fallback функции для совместимости
    def get_logger():
        import logging
        return logging.getLogger("system")
    def log_info(msg, **kwargs):
        print(f"INFO: {msg}")
    def log_warning(msg, **kwargs):
        print(f"WARNING: {msg}")
    def log_error(msg, **kwargs):
        print(f"ERROR: {msg}")
    def log_debug(msg, **kwargs):
        print(f"DEBUG: {msg}")

load_dotenv()

# Claude API
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

# OpenAI API (GPT)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AITUNNEL_API_KEY = os.getenv("AITUNNEL_API_KEY", "sk-aitunnel-ojv0bmY2HM2JN5ccC99FKfNi5YSaqvt1")
AITUNNEL_BASE_URL = "https://api.aitunnel.ru/v1/"

# Флаг для использования локального анализатора (только в крайнем случае)
USE_LOCAL_FALLBACK = os.getenv("AI_USE_LOCAL_FALLBACK", "false").lower() == "true"


def analyze_match_with_ai(match: Dict, sport: str = "football") -> Optional[Dict]:
    """
    Анализирует матч через GPT.
    
    КРИТИЧЕСКОЕ ТРЕБОВАНИЕ: GPT анализ должен применяться к каждому прогону!
    
    Приоритет:
    1. GPT через AITunnel (если доступен) - ПРИОРИТЕТ
    2. GPT API напрямую (если доступен) - ПРИОРИТЕТ
    3. Локальный анализатор (только если USE_LOCAL_FALLBACK=True)
    4. None (если ничего не доступно)
    
    Claude отключен - не используется.
    
    Args:
        match: Словарь с данными матча
        sport: Вид спорта
    
    Returns:
        Словарь с результатами анализа или None
    """
    # КРИТИЧЕСКОЕ: Используем ТОЛЬКО AITunnel GPT (Claude отключен)
    # GPT анализ должен применяться к каждому прогону - это важно!
    if OPENAI_AVAILABLE and (AITUNNEL_API_KEY or OPENAI_API_KEY):
        result = _analyze_with_gpt(match, sport)
        if result:
            return result
    
    # Claude ОТКЛЮЧЕН - не используем
    # if AITUNNEL_API_KEY:
    #     result = _analyze_with_claude_aitunnel(match, sport)
    #     if result:
    #         return result
    # 
    # if ANTHROPIC_AVAILABLE and ANTHROPIC_API_KEY:
    #     result = _analyze_with_claude(match, sport)
    #     if result:
    #         return result
    
    # Локальный анализатор как fallback (автоматически, если API недоступны или не работают)
    # Используем локальный анализатор, если:
    # 1. Явно разрешен через USE_LOCAL_FALLBACK
    # 2. API ключи отсутствуют
    # 3. API ключи есть, но не работают (вернули None)
    use_local = USE_LOCAL_FALLBACK or (not ANTHROPIC_API_KEY and not OPENAI_API_KEY) or True  # Всегда используем как fallback
    
    if use_local:
        try:
            from claude_local_analyzer import analyze_match_local
            result = analyze_match_local(match, sport)
            # Помечаем, что это локальный анализ
            if result:
                result["ai_source"] = "local_analyzer"
                # Логируем только если API ключи отсутствуют (чтобы не спамить)
                if not ANTHROPIC_API_KEY and not OPENAI_API_KEY:
                    log_debug(f"Using local analyzer for {match.get('slug', 'unknown')} (API keys not available)")
            return result
        except ImportError:
            pass
    
    log_warning(f"No AI analysis available for match {match.get('slug', 'unknown')}")
    return None


def analyze_matches_batch(matches: List[Dict], sport: str = "football") -> List[Dict]:
    """
    Анализирует батч матчей через GPT через AITunnel.
    
    КРИТИЧЕСКОЕ ТРЕБОВАНИЕ: GPT анализ должен применяться к КАЖДОМУ матчу!
    
    Защита от перегрузки: очередь из 3 одновременных запросов.
    
    Args:
        matches: Список матчей
        sport: Вид спорта
    
    Returns:
        Список матчей с добавленными полями от GPT
    """
    if not matches:
        log_debug("No matches to analyze")
        return matches
    
    log_info(f"🚀 Starting AI batch analysis: {len(matches)} matches for {sport}")
    
    import threading
    from queue import Queue
    
    # Очередь для ограничения одновременных запросов (максимум 3)
    MAX_CONCURRENT = 3
    semaphore = threading.Semaphore(MAX_CONCURRENT)
    results_queue = Queue()
    
    def analyze_single_match(match: Dict, sport: str, index: int):
        """Анализирует один матч с защитой от перегрузки"""
        with semaphore:  # Ограничиваем количество одновременных запросов
            try:
                teams = match.get('teams', ['?', '?'])
                match_slug = match.get('slug', 'unknown')
                log_info(f"🔍 Sending match {index+1}/{len(matches)} to AI: {teams[0]} vs {teams[1]} ({match_slug})")
                ai_result = analyze_match_with_ai(match, sport)
                if ai_result:
                    ai_source = ai_result.get("ai_source", "unknown")
                    prob = ai_result.get("claude_probability", "?")
                    log_info(f"✅ AI analysis SUCCESS for {teams[0]} vs {teams[1]}: {prob}% (source: {ai_source})")
                else:
                    log_warning(f"❌ AI analysis FAILED for {teams[0]} vs {teams[1]} ({match_slug}): returned None")
                results_queue.put((index, match, ai_result))
            except Exception as e:
                teams = match.get('teams', ['?', '?'])
                log_error(f"❌ AI analysis EXCEPTION for {teams[0]} vs {teams[1]}: {e}")
                results_queue.put((index, match, None))
    
    # Запускаем анализ в отдельных потоках (с ограничением)
    threads = []
    for i, match in enumerate(matches):
        thread = threading.Thread(target=analyze_single_match, args=(match, sport, i))
        thread.daemon = True
        thread.start()
        threads.append(thread)
    
    # Ждем завершения всех потоков (максимум 60 секунд на все матчи)
    for thread in threads:
        thread.join(timeout=60)
    
    # Собираем результаты
    analyzed_matches = []
    failed_count = 0
    results_dict = {}
    
    # Собираем все результаты из очереди
    while not results_queue.empty():
        index, match, ai_result = results_queue.get()
        results_dict[index] = (match, ai_result)
    
    # Обрабатываем результаты в правильном порядке
    for i in range(len(matches)):
        if i in results_dict:
            match, ai_result = results_dict[i]
        else:
            # Результат не получен (таймаут или ошибка)
            match = matches[i]
            ai_result = None
        
        if ai_result:
            # Применяем результаты GPT к матчу
            match.update({
                "claude_probability": ai_result.get("claude_probability"),
                "claude_recommendation": ai_result.get("claude_recommendation", ""),
                "claude_factors": ai_result.get("claude_factors", []),
                "claude_recommended": ai_result.get("claude_recommended", True),
                "ai_source": ai_result.get("ai_source", "aitunnel_gpt"),
                "validation_passed": ai_result.get("validation_passed", True),  # Флаг валидации
            })
            analyzed_matches.append(match)
        else:
            # КРИТИЧЕСКОЕ ИЗМЕНЕНИЕ: ВСЕ матчи должны быть возвращены, даже если GPT анализ не удался
            # Помечаем матч как недоступный для GPT анализа, но продолжаем обработку
            failed_count += 1
            teams = match.get("teams", ["?", "?"])
            teams_str = f"{teams[0]} vs {teams[1]}" if isinstance(teams, list) else str(teams)
            slug = match.get("slug", "unknown")
            log_warning(f"⚠️ GPT analysis failed for match {teams_str} ({slug}) - marking as unavailable")
            
            # Помечаем матч, что GPT анализ не был выполнен
            match.update({
                "gpt_analysis_unavailable": True,
                "gpt_unavailable_reason": "GPT analysis failed (timeout or API error)",
            })
            # ВАЖНО: Добавляем матч в список, даже если GPT анализ не удался
            # Это гарантирует, что ВСЕ матчи будут обработаны
            analyzed_matches.append(match)
    
    if failed_count > 0:
        log_warning(f"⚠️ GPT analysis failed for {failed_count} matches out of {len(matches)}")
    
    log_info(f"📊 AI batch analysis complete: {len(analyzed_matches)}/{len(matches)} matches successfully analyzed")
    return analyzed_matches


def _analyze_with_claude(match: Dict, sport: str) -> Optional[Dict]:
    """Анализирует матч через Claude API"""
    try:
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
        prompt = _build_analysis_prompt(match, sport)
        
        message = client.messages.create(
            model="claude-3-5-sonnet",  # Актуальная модель (без даты)
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Безопасная проверка ответа Claude
        if not message or not hasattr(message, 'content') or not message.content:
            log_warning(f"Claude API returned no content for {match.get('slug', 'unknown')}")
            return None
        
        if len(message.content) == 0:
            log_warning(f"Claude API returned empty content array for {match.get('slug', 'unknown')}")
            return None
        
        if not hasattr(message.content[0], 'text') or not message.content[0].text:
            log_warning(f"Claude API content has no text for {match.get('slug', 'unknown')}")
            return None
        
        response_text = message.content[0].text
        result = _parse_ai_response(response_text, match)
        
        if result:
            result["ai_source"] = "claude_api"
        
        return result
        
    except Exception as e:
        log_warning(f"Claude API failed: {e}")
        return None


def _analyze_with_claude_aitunnel(match: Dict, sport: str) -> Optional[Dict]:
    """Анализирует матч через Claude API через AITunnel"""
    try:
        if not AITUNNEL_API_KEY:
            return None
        
        # Claude через AITunnel использует OpenAI-совместимый интерфейс
        client = OpenAI(
            api_key=AITUNNEL_API_KEY,
            base_url=AITUNNEL_BASE_URL
        )
        prompt = _build_analysis_prompt(match, sport)
        
        # Используем Claude через AITunnel (claude-3-5-sonnet или claude-3-opus)
        # Пробуем сначала sonnet (быстрее и дешевле), затем opus (лучше качество)
        models_to_try = ["claude-3-5-sonnet", "claude-3-opus", "claude-3-sonnet"]
        
        for model in models_to_try:
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "Ты эксперт по анализу спортивных матчей. Анализируй матчи объективно и давай точные оценки вероятности."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=500,
                    temperature=0.3
                )
                
                # Безопасная проверка ответа
                if not response or not hasattr(response, 'choices') or not response.choices or len(response.choices) == 0:
                    log_warning(f"Claude AITunnel API returned invalid response for {match.get('slug', 'unknown')}")
                    continue
                
                choice = response.choices[0]
                if not hasattr(choice, 'message') or not choice.message or not hasattr(choice.message, 'content') or not choice.message.content:
                    log_warning(f"Claude AITunnel API response has no content for {match.get('slug', 'unknown')}")
                    continue
                
                response_text = choice.message.content
                result = _parse_ai_response(response_text, match)
                
                if result:
                    result["ai_source"] = f"aitunnel_claude_{model}"
                
                return result
            except Exception as e:
                # Пробуем следующую модель
                continue
        
        return None
        
    except Exception as e:
        log_warning(f"Claude AITunnel API failed: {e}")
        return None


def _analyze_with_gpt(match: Dict, sport: str) -> Optional[Dict]:
    """Анализирует матч через GPT API (через AITunnel или напрямую)"""
    import signal
    from contextlib import contextmanager
    
    @contextmanager
    def timeout_context(seconds):
        """Контекстный менеджер для таймаута (Windows-совместимый)"""
        # Для Windows используем threading.Timer вместо signal
        import threading
        
        class TimeoutError(Exception):
            pass
        
        timer = None
        def timeout_handler():
            raise TimeoutError(f"GPT API timeout after {seconds} seconds")
        
        timer = threading.Timer(seconds, timeout_handler)
        timer.start()
        try:
            yield
        except TimeoutError:
            raise
        finally:
            if timer:
                timer.cancel()
    
    try:
        # Приоритет: AITunnel (если ключ есть), затем обычный OpenAI
        api_key = AITUNNEL_API_KEY if AITUNNEL_API_KEY else OPENAI_API_KEY
        base_url = AITUNNEL_BASE_URL if AITUNNEL_API_KEY else None
        
        if not api_key:
            teams = match.get('teams', ['?', '?'])
            teams_str = f"{teams[0]} vs {teams[1]}"
            log_error(f"🚨 КРИТИЧЕСКАЯ ОШИБКА: Нет API ключа для GPT анализа матча {teams_str}")
            log_error(f"🚨 AITUNNEL_API_KEY: {bool(AITUNNEL_API_KEY)}, OPENAI_API_KEY: {bool(OPENAI_API_KEY)}")
            return None
        
        teams = match.get('teams', ['?', '?'])
        log_debug(f"📡 Calling GPT API for {teams[0]} vs {teams[1]} (via {'AITunnel' if base_url else 'OpenAI'})")
        
        client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=10.0  # Таймаут 10 секунд для запроса
        )
        prompt = _build_analysis_prompt(match, sport)
        
        # Используем gpt-4o для лучшего качества анализа (более точные прогнозы)
        # gpt-4o-mini слишком простая для такого важного анализа
        model = "gpt-4o" if base_url else "gpt-4o"
        
        # Защита от таймаута: максимум 10 секунд на запрос
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Ты эксперт по анализу спортивных матчей. Анализируй матчи объективно и давай точные оценки вероятности."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3  # Низкая температура для более детерминированных ответов
            )
        except Exception as timeout_error:
            teams = match.get('teams', ['?', '?'])
            teams_str = f"{teams[0]} vs {teams[1]}"
            slug = match.get('slug', 'unknown')
            log_error(f"🚨 КРИТИЧЕСКАЯ ОШИБКА: GPT API таймаут или ошибка для {teams_str} ({slug})")
            log_error(f"🚨 Тип ошибки: {type(timeout_error).__name__}")
            log_error(f"🚨 Сообщение ошибки: {str(timeout_error)}")
            import traceback
            log_error(f"🚨 Traceback:\n{traceback.format_exc()}")
            return None
        
        # Безопасная проверка ответа
        if not response:
            log_warning(f"GPT API returned None response for {match.get('slug', 'unknown')}")
            return None
        
        if not hasattr(response, 'choices') or not response.choices:
            log_warning(f"GPT API response has no choices for {match.get('slug', 'unknown')}")
            return None
        
        if len(response.choices) == 0:
            log_warning(f"GPT API response has empty choices array for {match.get('slug', 'unknown')}")
            return None
        
        # Безопасное извлечение choice
        try:
            choice = response.choices[0]
        except (IndexError, TypeError, AttributeError) as e:
            log_warning(f"GPT API response: cannot access choices[0] for {match.get('slug', 'unknown')}: {e}")
            return None
        
        if not choice or not hasattr(choice, 'message') or not choice.message:
            log_warning(f"GPT API response choice has no message for {match.get('slug', 'unknown')}")
            return None
        
        if not hasattr(choice.message, 'content') or not choice.message.content:
            log_warning(f"GPT API response message has no content for {match.get('slug', 'unknown')}")
            return None
        
        # Безопасное извлечение content
        try:
            response_text = choice.message.content
            if not response_text or not isinstance(response_text, str):
                log_warning(f"GPT API response content is invalid for {match.get('slug', 'unknown')}: {type(response_text)}")
                return None
        except (AttributeError, TypeError) as e:
            log_warning(f"GPT API response: cannot access message.content for {match.get('slug', 'unknown')}: {e}")
            return None
        teams = match.get('teams', ['?', '?'])
        teams_str = f"{teams[0]} vs {teams[1]}"
        log_debug(f"📥 GPT API response received for {teams_str}")
        
        # Детальное логирование полного ответа GPT для диагностики
        log_debug(f"📋 Полный ответ GPT для {teams_str}:\n{response_text}")
        
        result = _parse_ai_response(response_text, match)
        
        if result:
            result["ai_source"] = "aitunnel_gpt" if base_url else "gpt_api"
            prob = result.get('claude_probability')
            rec = result.get('claude_recommended', True)
            rec_text = result.get('claude_recommendation', '')
            
            log_debug(f"✅ GPT response parsed: probability={prob}%, recommended={rec}")
            
            # Детальное логирование, если матч не рекомендуется
            if not rec:
                log_warning(f"🚫 GPT НЕ РЕКОМЕНДУЕТ {teams_str}:")
                log_warning(f"   Вероятность: {prob}%")
                log_warning(f"   Текст рекомендации: {rec_text[:200] if rec_text else 'нет'}")
                log_warning(f"   Полный ответ GPT: {response_text[:500]}")
            
            # Применяем мягкую валидацию (не исключаем матч, только помечаем)
            try:
                from gpt_analysis_validator import apply_soft_validation
                result = apply_soft_validation(match, result)
                
                # Логируем предупреждения, но не исключаем матч
                if not result.get("validation_passed", True):
                    warning = result.get("validation_warning", "Unknown validation issue")
                    log_warning(f"GPT validation warning for {match.get('slug', 'unknown')}: {warning}")
            except ImportError:
                # Валидатор не доступен - продолжаем без него
                pass
        
        return result
        
    except Exception as e:
        teams = match.get('teams', ['?', '?'])
        teams_str = f"{teams[0]} vs {teams[1]}"
        slug = match.get('slug', 'unknown')
        log_error(f"🚨 КРИТИЧЕСКАЯ ОШИБКА: GPT API failed для {teams_str} ({slug})")
        log_error(f"🚨 Тип ошибки: {type(e).__name__}")
        log_error(f"🚨 Сообщение ошибки: {str(e)}")
        import traceback
        log_error(f"🚨 Traceback:\n{traceback.format_exc()}")
        return None


def _build_analysis_prompt(match: Dict, sport: str) -> str:
    """Строит промпт для ИИ на основе данных матча"""
    teams = match.get("teams", ["", ""])
    score = match.get("score", "0:0")
    minute = match.get("minute", "—")
    leader_idx = match.get("leader_index", 0)
    leader_name = teams[leader_idx] if leader_idx < len(teams) else ""
    
    # КРИТИЧЕСКОЕ: НЕ используем коэффициенты в анализе GPT
    # Анализируем ТОЛЬКО на основе статистики матча (счет, удары, владение, xG и т.д.)
    # Коэффициенты не должны влиять на оценку вероятности GPT
    odds_warning = ""
    if match.get("odds_corrected") or match.get("odds_info"):
        odds_warning = "\n⚠️ ВАЖНО: В данных могут присутствовать коэффициенты от букмекеров. ИГНОРИРУЙ их полностью! Анализируй ТОЛЬКО на основе статистики матча (счет, удары, владение, xG и т.д.). Коэффициенты не должны влиять на твою оценку вероятности."
    
    # Проверка качества данных и предупреждения GPT
    try:
        from data_quality_validator import build_data_quality_warning, get_data_quality_score
        data_quality_warning = build_data_quality_warning(match, sport)
        data_quality_score = get_data_quality_score(match, sport)
        
        # Добавляем предупреждение о качестве данных в промпт
        if data_quality_warning:
            odds_warning += data_quality_warning
        
        # Сохраняем оценку качества данных в матч для дальнейшего использования
        match["data_quality_score"] = data_quality_score
    except ImportError:
        # Модуль валидации не доступен - продолжаем без него
        data_quality_warning = ""
        data_quality_score = 1.0
        match["data_quality_score"] = 1.0
    
    if sport == "football":
        leader_metrics = match.get("leader_metrics", {})
        trailing_metrics = match.get("trailing_metrics", {})
        
        # Дополнительная информация для более точного анализа
        tournament = match.get("tournament") or match.get("tournament_name", "Неизвестно")
        league_tier = match.get("league_tier", "unknown")
        minute_numeric = match.get("minute_numeric")
        
        # Вычисляем разницу в метриках для анализа
        xg_diff = leader_metrics.get('xg', 0) - trailing_metrics.get('xg', 0) if leader_metrics.get('xg') and trailing_metrics.get('xg') else None
        shots_diff = leader_metrics.get('shots_on_target', 0) - trailing_metrics.get('shots_on_target', 0) if leader_metrics.get('shots_on_target') is not None and trailing_metrics.get('shots_on_target') is not None else None
        possession_diff = leader_metrics.get('possession', 0) - trailing_metrics.get('possession', 0) if leader_metrics.get('possession') is not None and trailing_metrics.get('possession') is not None else None
        
        prompt = f"""Проанализируй live-матч по футболу и оцени вероятность победы лидера. БУДЬ МАКСИМАЛЬНО СКРУПУЛЕЗНЫМ И КРИТИЧНЫМ.

МАТЧ: {teams[0]} - {teams[1]}
ТУРНИР: {tournament} (уровень: {league_tier})
СЧЕТ: {score} ({minute}')
ЛИДЕР: {leader_name}
{odds_warning}

СТАТИСТИКА ЛИДЕРА:
- xG: {leader_metrics.get('xg', 'N/A')}
- Удары в створ: {leader_metrics.get('shots_on_target', 'N/A')}
- Всего ударов: {leader_metrics.get('shots_total', 'N/A')}
- Владение: {leader_metrics.get('possession', 'N/A')}%

СТАТИСТИКА ОТСТАЮЩЕГО:
- xG: {trailing_metrics.get('xg', 'N/A')}
- Удары в створ: {trailing_metrics.get('shots_on_target', 'N/A')}
- Всего ударов: {trailing_metrics.get('shots_total', 'N/A')}
- Владение: {trailing_metrics.get('possession', 'N/A')}%

РАЗНИЦА В МЕТРИКАХ:
- Разница xG: {xg_diff if xg_diff is not None else 'N/A'}
- Разница ударов в створ: {shots_diff if shots_diff is not None else 'N/A'}
- Разница владения: {possession_diff if possession_diff is not None else 'N/A'}%

КРИТИЧЕСКИ ВАЖНЫЕ ПРОВЕРКИ (выполни все):
1. ✅ Проверь, что xG лидера ЗНАЧИТЕЛЬНО выше xG отстающего (минимум +0.3 разницы)
2. ✅ Проверь, что счет СООТВЕТСТВУЕТ xG (если xG лидера 1.5, а счет 1:0 - это нормально, но если xG 0.3, а счет 2:0 - подозрительно)
3. ✅ Проверь время матча: на {minute_numeric if minute_numeric else 'N/A'}' матча лидер должен иметь УСТОЙЧИВОЕ преимущество
4. ✅ Проверь удары в створ: лидер должен иметь минимум 2+ удара в створ больше отстающего
5. ✅ Проверь владение: если владение лидера < 50%, это ПЛОХОЙ знак даже при счете в его пользу
6. ✅ Проверь динамику: если отстающий создает больше моментов в последние 10-15 минут - это ОПАСНО
7. ✅ Проверь контекст турнира: {league_tier} уровень - учитывай качество лиги

ЗАДАЧА:
1. Оцени реальную вероятность победы лидера ТОЛЬКО на основе статистики матча (ИГНОРИРУЙ коэффициенты)
2. БУДЬ КРИТИЧНЫМ: если есть ЛЮБЫЕ сомнения - НЕ рекомендовать матч
3. ВАЖНО: Рекомендуй матч ТОЛЬКО если вероятность в диапазоне 65%-90% (ужесточенный диапазон)
4. Если вероятность меньше 65% или больше 90% - ОБЯЗАТЕЛЬНО напиши "НЕ РЕКОМЕНДУЕТСЯ"
5. Если разница в xG меньше 0.3 - НЕ рекомендовать
6. Если счет не соответствует xG (большая разница) - НЕ рекомендовать
7. Если владение лидера < 50% - НЕ рекомендовать
8. Укажи ВСЕ ключевые факторы, включая негативные (что может пойти не так)
9. Дай детальную рекомендацию с обоснованием на основе ТОЛЬКО статистики матча

ФОРМАТ ОТВЕТА (строго):
ВЕРОЯТНОСТЬ: [число]%
ФАКТОРЫ: [список ВСЕХ факторов через запятую, включая негативные]
РЕКОМЕНДАЦИЯ: [детальный текст с обоснованием. Если вероятность вне диапазона 65-90% ИЛИ есть сомнения - напиши "НЕ РЕКОМЕНДУЕТСЯ"]"""
    
    elif sport == "tennis":
        sets_score = match.get("sets_score", "0:0")
        current_games = match.get("current_games", (0, 0))
        current_set = match.get("current_set", 1)
        points = match.get("points", (0, 0))
        sets_home, sets_away = sets_score.split(":") if ":" in sets_score else ("0", "0")
        sets_home_int = int(sets_home) if sets_home.isdigit() else 0
        sets_away_int = int(sets_away) if sets_away.isdigit() else 0
        games_diff = abs(current_games[0] - current_games[1]) if len(current_games) == 2 else 0
        
        prompt = f"""Проанализируй live-матч по теннису и оцени вероятность победы лидера. БУДЬ МАКСИМАЛЬНО СКРУПУЛЕЗНЫМ И КРИТИЧНЫМ.

МАТЧ: {teams[0]} - {teams[1]}
СЧЕТ ПО СЕТАМ: {sets_score}
ТЕКУЩИЙ СЕТ: {current_set} ({current_games[0]}:{current_games[1]})
ЛИДЕР: {leader_name}
ОЧКИ: {points[0]} - {points[1]}
{odds_warning}

КРИТИЧЕСКИ ВАЖНЫЕ ПРОВЕРКИ (выполни все):
1. ✅ Проверь счет по сетам: лидер должен вести минимум 2:0 или 2:1 (НЕ 1:1!)
2. ✅ Проверь разницу в текущем сете: лидер должен вести минимум с разницей в 2 гейма (например, 4:2, 5:3)
3. ✅ Проверь брейк-пойнты: лидер должен иметь преимущество в реализации брейков
4. ✅ Проверь эйсы: если отстающий имеет больше эйсов - это опасный знак
5. ✅ Проверь динамику: если отстающий выигрывает геймы быстрее - это опасно
6. ✅ Проверь психологию: если счет по сетам 1:1 - это слишком рискованно

ЗАДАЧА:
1. Оцени реальную вероятность победы лидера ТОЛЬКО на основе статистики матча (ИГНОРИРУЙ коэффициенты)
2. БУДЬ КРИТИЧНЫМ: если есть ЛЮБЫЕ сомнения - НЕ рекомендовать матч
3. ВАЖНО: Рекомендуй матч ТОЛЬКО если вероятность в диапазоне 65%-90% (ужесточенный диапазон)
4. Если счет по сетам 1:1 - ОБЯЗАТЕЛЬНО напиши "НЕ РЕКОМЕНДУЕТСЯ"
5. Если разница в текущем сете < 2 гейма - ОБЯЗАТЕЛЬНО напиши "НЕ РЕКОМЕНДУЕТСЯ"
6. Если вероятность меньше 65% или больше 90% - ОБЯЗАТЕЛЬНО напиши "НЕ РЕКОМЕНДУЕТСЯ"
7. Укажи ВСЕ ключевые факторы, включая негативные (что может пойти не так)
8. Дай детальную рекомендацию с обоснованием на основе ТОЛЬКО статистики матча

ФОРМАТ ОТВЕТА (строго):
ВЕРОЯТНОСТЬ: [число]%
ФАКТОРЫ: [список ВСЕХ факторов через запятую, включая негативные]
РЕКОМЕНДАЦИЯ: [детальный текст с обоснованием. Если вероятность вне диапазона 65-90% ИЛИ счет 1:1 ИЛИ разница < 2 гейма ИЛИ есть сомнения - напиши "НЕ РЕКОМЕНДУЕТСЯ"]"""
    
    elif sport == "basketball":
        leader_metrics = match.get("leader_metrics", {})
        trailing_metrics = match.get("trailing_metrics", {})
        minute_numeric = match.get("minute_numeric", 0)
        score_home, score_away = score.split(":") if ":" in score else ("0", "0")
        score_home_int = int(score_home) if score_home.isdigit() else 0
        score_away_int = int(score_away) if score_away.isdigit() else 0
        score_diff = abs(score_home_int - score_away_int)
        points_leader = leader_metrics.get('points', 0) or 0
        points_trailing = trailing_metrics.get('points', 0) or 0
        rebounds_leader = leader_metrics.get('rebounds', 0) or 0
        rebounds_trailing = trailing_metrics.get('rebounds', 0) or 0
        rebounds_diff = rebounds_leader - rebounds_trailing
        fg_pct_leader = leader_metrics.get('field_goal_pct', 0) or 0
        fg_pct_trailing = trailing_metrics.get('field_goal_pct', 0) or 0
        
        prompt = f"""Проанализируй live-матч по баскетболу и оцени вероятность победы лидера. БУДЬ МАКСИМАЛЬНО СКРУПУЛЕЗНЫМ И КРИТИЧНЫМ.

МАТЧ: {teams[0]} - {teams[1]}
СЧЕТ: {score} ({minute}')
ЛИДЕР: {leader_name}
{odds_warning}

СТАТИСТИКА ЛИДЕРА:
- Очки: {leader_metrics.get('points', 'N/A')}
- Подборы: {leader_metrics.get('rebounds', 'N/A')}
- Передачи: {leader_metrics.get('assists', 'N/A')}
- % попаданий: {leader_metrics.get('field_goal_pct', 'N/A')}%

СТАТИСТИКА ОТСТАЮЩЕГО:
- Очки: {trailing_metrics.get('points', 'N/A')}
- Подборы: {trailing_metrics.get('rebounds', 'N/A')}
- Передачи: {trailing_metrics.get('assists', 'N/A')}
- % попаданий: {trailing_metrics.get('field_goal_pct', 'N/A')}%

КРИТИЧЕСКИ ВАЖНЫЕ ПРОВЕРКИ (выполни все):
1. ✅ Проверь разницу в счете: лидер должен вести минимум с разницей в 6 очков (например, 45:39, 60:54)
2. ✅ Проверь время матча: на 30+ минуте разница должна быть минимум 8 очков
3. ✅ Проверь подборы: лидер должен иметь преимущество минимум +3 подбора
4. ✅ Проверь процент попаданий: лидер должен иметь выше процент (минимум +5%)
5. ✅ Проверь динамику: если отстающий набирает очки быстрее в последние 5 минут - это опасно
6. ✅ Проверь передачу: если отстающий имеет больше передач - это может указывать на активность

ЗАДАЧА:
1. Оцени реальную вероятность победы лидера ТОЛЬКО на основе статистики матча (ИГНОРИРУЙ коэффициенты)
2. БУДЬ КРИТИЧНЫМ: если есть ЛЮБЫЕ сомнения - НЕ рекомендовать матч
3. ВАЖНО: Рекомендуй матч ТОЛЬКО если вероятность в диапазоне 65%-90% (ужесточенный диапазон)
4. Если разница в счете < 6 очков - ОБЯЗАТЕЛЬНО напиши "НЕ РЕКОМЕНДУЕТСЯ"
5. Если на 30+ минуте разница < 8 очков - ОБЯЗАТЕЛЬНО напиши "НЕ РЕКОМЕНДУЕТСЯ"
6. Если разница в подборах < 3 - ОБЯЗАТЕЛЬНО напиши "НЕ РЕКОМЕНДУЕТСЯ"
7. Если вероятность меньше 65% или больше 90% - ОБЯЗАТЕЛЬНО напиши "НЕ РЕКОМЕНДУЕТСЯ"
8. Укажи ВСЕ ключевые факторы, включая негативные (что может пойти не так)
9. Дай детальную рекомендацию с обоснованием на основе ТОЛЬКО статистики матча

ФОРМАТ ОТВЕТА (строго):
ВЕРОЯТНОСТЬ: [число]%
ФАКТОРЫ: [список ВСЕХ факторов через запятую, включая негативные]
РЕКОМЕНДАЦИЯ: [детальный текст с обоснованием. Если вероятность вне диапазона 65-90% ИЛИ разница < 6 очков ИЛИ разница в подборах < 3 ИЛИ есть сомнения - напиши "НЕ РЕКОМЕНДУЕТСЯ"]"""
    
    elif sport == "volleyball":
        sets_score = match.get("sets_score", "0:0")
        current_set_score = match.get("current_set_score", (0, 0))
        current_set = match.get("current_set", 1)
        sets_home, sets_away = sets_score.split(":") if ":" in sets_score else ("0", "0")
        sets_home_int = int(sets_home) if sets_home.isdigit() else 0
        sets_away_int = int(sets_away) if sets_away.isdigit() else 0
        points_diff = abs(current_set_score[0] - current_set_score[1]) if len(current_set_score) == 2 else 0
        
        prompt = f"""Проанализируй live-матч по волейболу и оцени вероятность победы лидера. БУДЬ МАКСИМАЛЬНО СКРУПУЛЕЗНЫМ И КРИТИЧНЫМ.

МАТЧ: {teams[0]} - {teams[1]}
СЧЕТ ПО СЕТАМ: {sets_score}
ТЕКУЩИЙ СЕТ: {current_set} ({current_set_score[0]}:{current_set_score[1]})
ЛИДЕР: {leader_name}
{odds_warning}

КРИТИЧЕСКИ ВАЖНЫЕ ПРОВЕРКИ (выполни все):
1. ✅ Проверь счет по сетам: лидер должен вести минимум 2:0 или 2:1 (НЕ 1:1!)
2. ✅ Проверь разницу в текущем сете: лидер должен вести минимум с разницей в 3 очка (например, 20:17, 22:19)
3. ✅ Проверь атаки: лидер должен иметь преимущество в успешных атаках
4. ✅ Проверь блоки: если отстающий имеет больше блоков - это опасный знак
5. ✅ Проверь подачи: преимущество в эйсах - хороший знак
6. ✅ Проверь динамику: если отстающий набирает очки быстрее - это опасно

ЗАДАЧА:
1. Оцени реальную вероятность победы лидера ТОЛЬКО на основе статистики матча (ИГНОРИРУЙ коэффициенты)
2. БУДЬ КРИТИЧНЫМ: если есть ЛЮБЫЕ сомнения - НЕ рекомендовать матч
3. ВАЖНО: Рекомендуй матч ТОЛЬКО если вероятность в диапазоне 65%-90% (ужесточенный диапазон)
4. Если счет по сетам 1:1 - ОБЯЗАТЕЛЬНО напиши "НЕ РЕКОМЕНДУЕТСЯ"
5. Если разница в текущем сете < 3 очка - ОБЯЗАТЕЛЬНО напиши "НЕ РЕКОМЕНДУЕТСЯ"
6. Если вероятность меньше 65% или больше 90% - ОБЯЗАТЕЛЬНО напиши "НЕ РЕКОМЕНДУЕТСЯ"
7. Укажи ВСЕ ключевые факторы, включая негативные (что может пойти не так)
8. Дай детальную рекомендацию с обоснованием на основе ТОЛЬКО статистики матча

ФОРМАТ ОТВЕТА (строго):
ВЕРОЯТНОСТЬ: [число]%
ФАКТОРЫ: [список ВСЕХ факторов через запятую, включая негативные]
РЕКОМЕНДАЦИЯ: [детальный текст с обоснованием. Если вероятность вне диапазона 65-90% ИЛИ счет 1:1 ИЛИ разница < 3 очка ИЛИ есть сомнения - напиши "НЕ РЕКОМЕНДУЕТСЯ"]"""
    
    elif sport == "handball":
        score_home, score_away = score.split(":") if ":" in score else ("0", "0")
        score_home_int = int(score_home) if score_home.isdigit() else 0
        score_away_int = int(score_away) if score_away.isdigit() else 0
        score_diff = abs(score_home_int - score_away_int)
        minute_numeric = match.get("minute_numeric")
        
        prompt = f"""Проанализируй live-матч по гандболу и оцени вероятность победы лидера. БУДЬ МАКСИМАЛЬНО СКРУПУЛЕЗНЫМ И КРИТИЧНЫМ.

МАТЧ: {teams[0]} - {teams[1]}
СЧЕТ: {score} ({minute}')
ЛИДЕР: {leader_name}
{odds_warning}

КРИТИЧЕСКИ ВАЖНЫЕ ПРОВЕРКИ (выполни все):
1. ✅ Проверь разницу в счете: лидер должен вести минимум с разницей в 3 гола (например, 25:22, 30:27)
2. ✅ Проверь время матча: на 40+ минуте разница должна быть минимум 3 гола, на 45+ минуте - минимум 2 гола
3. ✅ Проверь броски в створ: лидер должен иметь преимущество минимум +2 броска в створ
4. ✅ Проверь процент реализации: лидер должен иметь выше процент реализации (минимум 50%)
5. ✅ Проверь динамику: если отстающий забивает быстрее в последние 5-10 минут - это опасно
6. ✅ Проверь общий счет: если общий счет < 20 голов - матч слишком ранний

ЗАДАЧА:
1. Оцени реальную вероятность победы лидера ТОЛЬКО на основе статистики матча (ИГНОРИРУЙ коэффициенты)
2. БУДЬ КРИТИЧНЫМ: если есть ЛЮБЫЕ сомнения - НЕ рекомендовать матч
3. ВАЖНО: Рекомендуй матч ТОЛЬКО если вероятность в диапазоне 65%-90% (ужесточенный диапазон)
4. Если разница в счете < 3 гола - ОБЯЗАТЕЛЬНО напиши "НЕ РЕКОМЕНДУЕТСЯ"
5. Если на 40+ минуте разница < 3 гола - ОБЯЗАТЕЛЬНО напиши "НЕ РЕКОМЕНДУЕТСЯ"
6. Если вероятность меньше 65% или больше 90% - ОБЯЗАТЕЛЬНО напиши "НЕ РЕКОМЕНДУЕТСЯ"
7. Укажи ВСЕ ключевые факторы, включая негативные (что может пойти не так)
8. Дай детальную рекомендацию с обоснованием на основе ТОЛЬКО статистики матча

ФОРМАТ ОТВЕТА (строго):
ВЕРОЯТНОСТЬ: [число]%
ФАКТОРЫ: [список ВСЕХ факторов через запятую, включая негативные]
РЕКОМЕНДАЦИЯ: [детальный текст с обоснованием. Если вероятность вне диапазона 65-90% ИЛИ разница < 3 гола ИЛИ есть сомнения - напиши "НЕ РЕКОМЕНДУЕТСЯ"]"""
    
    elif sport == "american_football":
        score_home, score_away = score.split(":") if ":" in score else ("0", "0")
        score_home_int = int(score_home) if score_home.isdigit() else 0
        score_away_int = int(score_away) if score_away.isdigit() else 0
        score_diff = abs(score_home_int - score_away_int)
        minute_numeric = match.get("minute_numeric")
        yards = match.get("yards")
        touchdowns = match.get("touchdowns")
        interceptions = match.get("interceptions")
        
        prompt = f"""Проанализируй live-матч по американскому футболу и оцени вероятность победы лидера. БУДЬ МАКСИМАЛЬНО СКРУПУЛЕЗНЫМ И КРИТИЧНЫМ.

МАТЧ: {teams[0]} - {teams[1]}
СЧЕТ: {score} ({minute}')
ЛИДЕР: {leader_name}
{odds_warning}

СТАТИСТИКА ЛИДЕРА:
- Ярды: {yards[0] if yards else 'N/A'}
- Тачдауны: {touchdowns[0] if touchdowns else 'N/A'}
- Перехваты: {interceptions[0] if interceptions else 'N/A'}

СТАТИСТИКА ОТСТАЮЩЕГО:
- Ярды: {yards[1] if yards else 'N/A'}
- Тачдауны: {touchdowns[1] if touchdowns else 'N/A'}
- Перехваты: {interceptions[1] if interceptions else 'N/A'}

КРИТИЧЕСКИ ВАЖНЫЕ ПРОВЕРКИ (выполни все):
1. ✅ Проверь разницу в счете: лидер должен вести минимум с разницей в 7 очков (тачдаун + экстрапоинт)
2. ✅ Проверь время матча: на 30+ минуте разница должна быть минимум 10 очков
3. ✅ Проверь ярды: лидер должен иметь преимущество минимум +50 ярдов
4. ✅ Проверь тачдауны: лидер должен иметь больше тачдаунов
5. ✅ Проверь перехваты: если отстающий имеет больше перехватов - это опасный знак
6. ✅ Проверь динамику: если отстающий набирает очки быстрее - это опасно

ЗАДАЧА:
1. Оцени реальную вероятность победы лидера ТОЛЬКО на основе статистики матча (ИГНОРИРУЙ коэффициенты)
2. БУДЬ КРИТИЧНЫМ: если есть ЛЮБЫЕ сомнения - НЕ рекомендовать матч
3. ВАЖНО: Рекомендуй матч ТОЛЬКО если вероятность в диапазоне 65%-90% (ужесточенный диапазон)
4. Если разница в счете < 7 очков - ОБЯЗАТЕЛЬНО напиши "НЕ РЕКОМЕНДУЕТСЯ"
5. Если на 30+ минуте разница < 10 очков - ОБЯЗАТЕЛЬНО напиши "НЕ РЕКОМЕНДУЕТСЯ"
6. Если разница в ярдах < 50 - ОБЯЗАТЕЛЬНО напиши "НЕ РЕКОМЕНДУЕТСЯ"
7. Если вероятность меньше 65% или больше 90% - ОБЯЗАТЕЛЬНО напиши "НЕ РЕКОМЕНДУЕТСЯ"
8. Укажи ВСЕ ключевые факторы, включая негативные (что может пойти не так)
9. Дай детальную рекомендацию с обоснованием на основе ТОЛЬКО статистики матча

ФОРМАТ ОТВЕТА (строго):
ВЕРОЯТНОСТЬ: [число]%
ФАКТОРЫ: [список ВСЕХ факторов через запятую, включая негативные]
РЕКОМЕНДАЦИЯ: [детальный текст с обоснованием. Если вероятность вне диапазона 65-90% ИЛИ разница < 7 очков ИЛИ разница в ярдах < 50 ИЛИ есть сомнения - напиши "НЕ РЕКОМЕНДУЕТСЯ"]"""
    
    elif sport == "dota2":
        maps_score = match.get("maps_score", "0:0")
        current_map_score = match.get("current_map_score", (0, 0))
        current_map = match.get("current_map", 1)
        game_time = match.get("game_time")
        maps_home, maps_away = maps_score.split(":") if ":" in maps_score else ("0", "0")
        maps_home_int = int(maps_home) if maps_home.isdigit() else 0
        maps_away_int = int(maps_away) if maps_away.isdigit() else 0
        kills_diff = abs(current_map_score[0] - current_map_score[1]) if len(current_map_score) == 2 else 0
        kills = match.get("kills")
        net_worth = match.get("net_worth") or match.get("gold")
        towers = match.get("towers")
        
        prompt = f"""Проанализируй live-матч по Dota 2 и оцени вероятность победы лидера в ТЕКУЩЕЙ КАРТЕ (раунде). БУДЬ МАКСИМАЛЬНО СКРУПУЛЕЗНЫМ И КРИТИЧНЫМ.

КРИТИЧЕСКИ ВАЖНО: Ставки делаются на победу в КОНКРЕТНОЙ КАРТЕ, а не во всем матче! На новой карте будут новые герои - предугадать исход очень трудно. Поэтому анализируем ТОЛЬКО текущую карту.

МАТЧ: {teams[0]} - {teams[1]}
СЧЕТ ПО КАРТАМ: {maps_score}
ТЕКУЩАЯ КАРТА: {current_map} ({current_map_score[0]}:{current_map_score[1]} убийств)
ВРЕМЯ ИГРЫ: {game_time if game_time else 'N/A'} минут
ЛИДЕР: {leader_name}
{odds_warning}

СТАТИСТИКА ЛИДЕРА (в текущей карте):
- Убийства: {kills[0] if kills else 'N/A'} (каждое убийство = 1000 монет)
- Net Worth (золото): {net_worth[0] if net_worth else 'N/A'} золота
- Башни: {towers[0] if towers else 'N/A'}

СТАТИСТИКА ОТСТАЮЩЕГО (в текущей карте):
- Убийства: {kills[1] if kills else 'N/A'} (каждое убийство = 1000 монет)
- Net Worth (золото): {net_worth[1] if net_worth else 'N/A'} золота
- Башни: {towers[1] if towers else 'N/A'}

КРИТИЧЕСКИ ВАЖНЫЕ ПРОВЕРКИ (выполни все):
1. ✅ Проверь разницу в убийствах: лидер должен вести минимум с разницей в 5 убийств
2. ✅ Проверь Net Worth: разница должна быть минимум +2000 золота
3. ✅ КРИТИЧНО: Если лидер ведет по убийствам и башням, но ОТСТАЕТ по золоту - это ПЛОХОЙ знак (слабая игра в лесу и фарме)
4. ✅ Проверь время игры: минимум 30 минут (раньше статистика нестабильна)
5. ✅ Проверь динамику: если отстающий набирает убийства быстрее - это опасно
6. ✅ Проверь башни: если отстающий уничтожил больше башен - это опасный знак
7. ✅ Учитывай счет по картам как дополнительный фактор: если команда играет сильно на каждой карте ({maps_score}) - это хороший знак, но НЕ обязательное условие

ЗАДАЧА:
1. Оцени реальную вероятность победы лидера в ТЕКУЩЕЙ КАРТЕ ТОЛЬКО на основе статистики матча (ИГНОРИРУЙ коэффициенты)
2. БУДЬ КРИТИЧНЫМ: если есть ЛЮБЫЕ сомнения - НЕ рекомендовать матч
3. ВАЖНО: Рекомендуй матч ТОЛЬКО если вероятность в диапазоне 65%-90% (ужесточенный диапазон)
4. Анализируй ход игры на ТЕКУЩЕЙ КАРТЕ - не важно сколько карт до этого было сыграно
5. Счет по картам ({maps_score}) можешь учитывать как дополнительный фактор (если команда реально играет сильно на каждой карте), но НЕ жди пока счет станет неничейным
6. Если разница в убийствах < 5 - ОБЯЗАТЕЛЬНО напиши "НЕ РЕКОМЕНДУЕТСЯ"
7. Если разница в Net Worth < 2000 - ОБЯЗАТЕЛЬНО напиши "НЕ РЕКОМЕНДУЕТСЯ"
8. Если лидер отстает по золоту (даже при преимуществе в убийствах) - ОБЯЗАТЕЛЬНО напиши "НЕ РЕКОМЕНДУЕТСЯ"
9. Если время игры < 30 минут - ОБЯЗАТЕЛЬНО напиши "НЕ РЕКОМЕНДУЕТСЯ"
10. Если вероятность меньше 65% или больше 90% - ОБЯЗАТЕЛЬНО напиши "НЕ РЕКОМЕНДУЕТСЯ"
11. Укажи ВСЕ ключевые факторы, включая негативные (что может пойти не так)
12. Дай детальную рекомендацию с обоснованием на основе ТОЛЬКО статистики матча

ФОРМАТ ОТВЕТА (строго):
ВЕРОЯТНОСТЬ: [число]%
ФАКТОРЫ: [список ВСЕХ факторов через запятую, включая негативные]
РЕКОМЕНДАЦИЯ: [детальный текст с обоснованием. Если вероятность вне диапазона 65-90% ИЛИ разница < 5 убийств ИЛИ разница в Net Worth < 2000 ИЛИ лидер отстает по золоту ИЛИ время < 30 минут ИЛИ есть сомнения - напиши "НЕ РЕКОМЕНДУЕТСЯ"]"""
    
    elif sport in ["csgo", "cs2", "counter-strike"]:
        maps_score = match.get("maps_score", "0:0")
        current_map_score = match.get("current_map_score", (0, 0))
        current_map = match.get("current_map", 1)
        maps_home, maps_away = maps_score.split(":") if ":" in maps_score else ("0", "0")
        maps_home_int = int(maps_home) if maps_home.isdigit() else 0
        maps_away_int = int(maps_away) if maps_away.isdigit() else 0
        rounds_diff = abs(current_map_score[0] - current_map_score[1]) if len(current_map_score) == 2 else 0
        kills = match.get("kills")
        economy = match.get("economy")
        
        prompt = f"""Проанализируй live-матч по Counter-Strike и оцени вероятность победы лидера. БУДЬ МАКСИМАЛЬНО СКРУПУЛЕЗНЫМ И КРИТИЧНЫМ.

МАТЧ: {teams[0]} - {teams[1]}
СЧЕТ ПО КАРТАМ: {maps_score}
ТЕКУЩАЯ КАРТА: {current_map} ({current_map_score[0]}:{current_map_score[1]})
ЛИДЕР: {leader_name}
{odds_warning}

СТАТИСТИКА ЛИДЕРА:
- Убийства: {kills[0] if kills else 'N/A'}
- Экономика: {economy[0] if economy else 'N/A'} долларов

СТАТИСТИКА ОТСТАЮЩЕГО:
- Убийства: {kills[1] if kills else 'N/A'}
- Экономика: {economy[1] if economy else 'N/A'} долларов

КРИТИЧЕСКИ ВАЖНЫЕ ПРОВЕРКИ (выполни все):
1. ✅ Проверь счет по картам: лидер должен вести минимум 1:0 (для BO3) или 2:0/2:1 (для BO5)
2. ✅ Проверь разницу в раундах: лидер должен вести минимум с разницей в 3 раунда (например, 10:7, 12:9)
3. ✅ Проверь экономику: лидер должен иметь больше денег (минимум +1000 долларов)
4. ✅ Проверь убийства: лидер должен иметь больше убийств
5. ✅ Проверь время карты: на 20+ раунде разница должна быть минимум 4 раунда
6. ✅ Проверь динамику: если отстающий выигрывает раунды быстрее - это опасно

ЗАДАЧА:
1. Оцени реальную вероятность победы лидера ТОЛЬКО на основе статистики матча (ИГНОРИРУЙ коэффициенты)
2. БУДЬ КРИТИЧНЫМ: если есть ЛЮБЫЕ сомнения - НЕ рекомендовать матч
3. ВАЖНО: Рекомендуй матч ТОЛЬКО если вероятность в диапазоне 65%-90% (ужесточенный диапазон)
4. Если счет по картам 0:0 или 1:1 - ОБЯЗАТЕЛЬНО напиши "НЕ РЕКОМЕНДУЕТСЯ"
5. Если разница в раундах < 3 - ОБЯЗАТЕЛЬНО напиши "НЕ РЕКОМЕНДУЕТСЯ"
6. Если отстающий имеет больше денег - ОБЯЗАТЕЛЬНО напиши "НЕ РЕКОМЕНДУЕТСЯ"
7. Если вероятность меньше 65% или больше 90% - ОБЯЗАТЕЛЬНО напиши "НЕ РЕКОМЕНДУЕТСЯ"
8. Укажи ВСЕ ключевые факторы, включая негативные (что может пойти не так)
9. Дай детальную рекомендацию с обоснованием на основе ТОЛЬКО статистики матча

ФОРМАТ ОТВЕТА (строго):
ВЕРОЯТНОСТЬ: [число]%
ФАКТОРЫ: [список ВСЕХ факторов через запятую, включая негативные]
РЕКОМЕНДАЦИЯ: [детальный текст с обоснованием. Если вероятность вне диапазона 65-90% ИЛИ счет 0:0/1:1 ИЛИ разница < 3 раунда ИЛИ есть сомнения - напиши "НЕ РЕКОМЕНДУЕТСЯ"]"""
    
    else:
        prompt = f"""Проанализируй live-матч и оцени вероятность победы лидера.

МАТЧ: {teams[0]} - {teams[1]}
СЧЕТ: {score} ({minute}')
ЛИДЕР: {leader_name}
{odds_warning}

ЗАДАЧА:
1. Оцени реальную вероятность победы лидера ТОЛЬКО на основе статистики матча
2. ВАЖНО: Рекомендуй матч если вероятность в диапазоне 55%-95% (расширенный диапазон для большего количества матчей)
3. Если вероятность меньше 55% или больше 95% - НЕ рекомендовать матч
4. Укажи ключевые факторы
5. Дай краткую рекомендацию

ФОРМАТ ОТВЕТА (строго):
ВЕРОЯТНОСТЬ: [число]%
ФАКТОРЫ: [список факторов через запятую]
РЕКОМЕНДАЦИЯ: [текст. Если вероятность вне диапазона 55-95%, напиши "НЕ РЕКОМЕНДУЕТСЯ"]"""
    
    return prompt


def _parse_ai_response(response_text: str, match: Dict) -> Optional[Dict]:
    """Парсит ответ ИИ и возвращает структурированные данные"""
    import re
    
    probability = None
    factors = []
    recommendation = ""
    recommended = True
    
    # Извлекаем вероятность
    prob_match = re.search(r'ВЕРОЯТНОСТЬ:\s*(\d+(?:\.\d+)?)%', response_text, re.IGNORECASE)
    if prob_match:
        probability = float(prob_match.group(1))
    
    # Извлекаем факторы
    factors_match = re.search(r'ФАКТОРЫ:\s*(.+?)(?:\n|РЕКОМЕНДАЦИЯ:)', response_text, re.IGNORECASE | re.DOTALL)
    if factors_match:
        factors_str = factors_match.group(1).strip()
        factors = [f.strip() for f in factors_str.split(',') if f.strip()]
    
    # Извлекаем рекомендацию
    rec_match = re.search(r'РЕКОМЕНДАЦИЯ:\s*(.+?)(?:\n|$)', response_text, re.IGNORECASE | re.DOTALL)
    if rec_match:
        recommendation = rec_match.group(1).strip()
    
    # КРИТИЧЕСКАЯ ПРОВЕРКА: Ищем "НЕ РЕКОМЕНДУЕТСЯ" во ВСЕМ ответе GPT, а не только в поле РЕКОМЕНДАЦИЯ
    # GPT может написать это в любом месте ответа
    response_upper = response_text.upper()
    not_recommended_patterns = [
        "НЕ РЕКОМЕНДУЕТСЯ",
        "НЕ РЕКОМЕНДУЮ",
        "НЕ РЕКОМЕНДОВАТЬ",
        "НЕ СТОИТ",
        "НЕ СОВЕТУЮ",
        "НЕ СОВЕТУЕТСЯ",
        "НЕ ПОДХОДИТ",
        "НЕ ПОДХОДИТ ДЛЯ СТАВКИ",
        "НЕ ПОДХОДИТ ДЛЯ РЕКОМЕНДАЦИИ",
        "НЕ РЕКОМЕНДУЕТСЯ ДЛЯ СТАВКИ",
        "НЕ РЕКОМЕНДУЕТСЯ ДЛЯ РЕКОМЕНДАЦИИ",
    ]
    
    # Проверяем все варианты формулировок "не рекомендуется"
    for pattern in not_recommended_patterns:
        if pattern in response_upper:
            recommended = False
            log_warning(f"🚫 Обнаружен паттерн '{pattern}' в ответе GPT - матч НЕ будет рекомендован")
            break
    
    # Дополнительная проверка: если в рекомендации явно написано "НЕ РЕКОМЕНДУЕТСЯ"
    if recommendation and "НЕ РЕКОМЕНДУЕТСЯ" in recommendation.upper():
        recommended = False
    
    # Проверяем диапазон вероятности (ужесточенный: 65-90% для футбола, тенниса, волейбола, гандбола, американского футбола)
    if probability is not None:
        sport = match.get("sport_type", "")
        # Строгий диапазон 65-90% для всех основных видов спорта
        strict_sports = ["football", "tennis", "basketball", "volleyball", "handball", "american_football", "dota2", "csgo", "cs2", "counter-strike"]
        if sport in strict_sports:
            if probability < 65 or probability > 90:
                recommended = False
                log_debug(f"🚫 Вероятность {probability}% вне диапазона 65-90% для {sport} - матч НЕ будет рекомендован")
        else:
            # Для остальных видов спорта - более мягкий диапазон (60-90%)
            if probability < 60 or probability > 90:
                recommended = False
                log_debug(f"🚫 Вероятность {probability}% вне диапазона 60-90% для {sport} - матч НЕ будет рекомендован")
    
    if probability is None:
        # КРИТИЧЕСКОЕ: Если вероятность не найдена, логируем полный ответ GPT для диагностики
        teams = match.get('teams', ['?', '?'])
        teams_str = f"{teams[0]} vs {teams[1]}"
        slug = match.get('slug', 'unknown')
        log_error(f"🚨 КРИТИЧЕСКАЯ ОШИБКА: GPT не вернул вероятность для {teams_str} ({slug})")
        log_error(f"🚨 Полный ответ GPT (первые 1000 символов):\n{response_text[:1000]}")
        log_error(f"🚨 Длина ответа: {len(response_text)} символов")
        log_error(f"🚨 Найдены факторы: {len(factors) > 0}")
        log_error(f"🚨 Найдена рекомендация: {len(recommendation) > 0}")
        return None
    
    # Возвращаем результат анализа GPT
    # Примечание: поля названы "claude_*" по историческим причинам, но используются для GPT
    return {
        "claude_probability": probability,  # Вероятность от GPT
        "claude_factors": factors,  # Факторы от GPT
        "claude_recommendation": recommendation,  # Рекомендация от GPT
        "claude_recommended": recommended,  # Рекомендует ли GPT (True/False)
    }

