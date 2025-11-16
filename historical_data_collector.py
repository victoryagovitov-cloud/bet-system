"""
Скрипт для выгрузки исторических данных через sportsipy
и склейки с нашими live-логами для ML baseline
"""

import os
import sys
import csv
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd

# Настройка UTF-8 для Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def check_sportsipy_installation():
    """Проверяет установку sportsipy"""
    try:
        import sportsipy
        print("✅ sportsipy установлен")
        return True
    except ImportError:
        print("❌ sportsipy не установлен")
        print("   Установите: pip install sportsipy")
        return False

def load_live_logs(log_file: str = "data/recommendations_log.csv") -> pd.DataFrame:
    """Загружает наши live-логи"""
    if not os.path.exists(log_file):
        print(f"⚠️  Файл {log_file} не найден")
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(log_file, encoding='utf-8')
        print(f"✅ Загружено {len(df)} записей из live-логов")
        return df
    except Exception as e:
        print(f"❌ Ошибка загрузки {log_file}: {e}")
        return pd.DataFrame()

def analyze_sportsipy_capabilities():
    """Анализирует возможности sportsipy для наших нужд"""
    if not check_sportsipy_installation():
        return None
    
    try:
        from sportsipy.nba.teams import Teams
        from sportsipy.nba.boxscore import Boxscore
        
        capabilities = {
            "available_sports": [],
            "data_types": [],
            "limitations": [],
            "recommendations": []
        }
        
        # Проверяем доступные модули
        import sportsipy
        print("\n📦 Доступные модули sportsipy:")
        
        # NBA (пример)
        try:
            teams = Teams()
            if teams:
                capabilities["available_sports"].append("NBA")
                capabilities["data_types"].append("Исторические матчи")
                capabilities["data_types"].append("Статистика команд")
                print("   ✅ NBA доступен")
        except Exception as e:
            print(f"   ⚠️  NBA: {e}")
        
        # Проверяем другие виды спорта
        # (sportsipy в основном для американских видов спорта)
        
        capabilities["limitations"] = [
            "Основной фокус на американских видах спорта (NBA, NFL, MLB, NHL)",
            "Ограниченная поддержка европейского футбола",
            "Нет live-данных",
            "Требует проверки доступности данных по нужным лигам"
        ]
        
        capabilities["recommendations"] = [
            "Использовать для baseline моделей по американским видам спорта (если расширимся)",
            "Для европейского футбола искать альтернативные источники",
            "Комбинировать с нашими live-логами для обучения моделей"
        ]
        
        return capabilities
        
    except Exception as e:
        print(f"❌ Ошибка анализа sportsipy: {e}")
        return None

def prepare_ml_dataset(live_logs_df: pd.DataFrame, output_file: str = "data/ml_baseline_dataset.csv"):
    """Подготавливает датасет для ML из live-логов"""
    if live_logs_df.empty:
        print("⚠️  Нет данных для подготовки датасета")
        return None
    
    # Фильтруем только записи с фактическими ставками (placed=1)
    # Проверяем наличие колонки placed
    if 'placed' in live_logs_df.columns:
        placed_bets = live_logs_df[live_logs_df['placed'].astype(str) == '1'].copy()
    else:
        placed_bets = pd.DataFrame()
    
    if placed_bets.empty:
        print("[INFO] Нет записей с placed=1, используем все записи для анализа")
        # Используем все записи для анализа
        placed_bets = live_logs_df.copy()
    
    # Создаём фичи для ML
    ml_features = []
    
    for _, row in placed_bets.iterrows():
        # Парсим счёт безопасно
        score_str = str(row.get('score', '0:0'))
        score_home = 0
        score_away = 0
        if ':' in score_str:
            try:
                parts = score_str.split(':')
                score_home = int(parts[0].strip().split()[0])
                score_away = int(parts[1].strip().split()[0])
            except (ValueError, IndexError):
                pass
        
        feature_row = {
            "timestamp": row.get('timestamp_msk', ''),
            "sport": row.get('sport', ''),
            "tournament": row.get('tournament', ''),
            "minute": row.get('minute_numeric', 0),
            "score_home": score_home,
            "score_away": score_away,
            "score_diff": 0,  # Вычислим ниже
            "bet_side": row.get('bet_side', ''),
            "coefficient": float(row.get('coefficient', 0)) if pd.notna(row.get('coefficient')) else 0,
            "probability": float(row.get('probability_percent', 0)) if pd.notna(row.get('probability_percent')) else 0,
            "dominance_score": float(row.get('dominance_score', 0)) if pd.notna(row.get('dominance_score')) else 0,
        }
        
        # Футбольные фичи
        if row.get('sport') == 'football':
            feature_row.update({
                "xg_home": float(row.get('xg_home', 0)) if pd.notna(row.get('xg_home')) else 0,
                "xg_away": float(row.get('xg_away', 0)) if pd.notna(row.get('xg_away')) else 0,
                "xg_diff": 0,  # Вычислим ниже
                "shots_on_target_home": float(row.get('shots_on_target_home', 0)) if pd.notna(row.get('shots_on_target_home')) else 0,
                "shots_on_target_away": float(row.get('shots_on_target_away', 0)) if pd.notna(row.get('shots_on_target_away')) else 0,
                "possession_home": float(row.get('possession_home', 0)) if pd.notna(row.get('possession_home')) else 0,
            })
        
        # Теннисные фичи
        if row.get('sport') == 'tennis':
            # Парсим теннисные данные безопасно (могут быть в формате "2/7")
            def safe_float_parse(val, default=0):
                if pd.isna(val):
                    return default
                try:
                    val_str = str(val)
                    if '/' in val_str:
                        # Формат "2/7" - берём первое число
                        return float(val_str.split('/')[0])
                    return float(val_str)
                except (ValueError, AttributeError):
                    return default
            
            feature_row.update({
                "tennis_points_home": safe_float_parse(row.get('tennis_points_home', 0)),
                "tennis_points_away": safe_float_parse(row.get('tennis_points_away', 0)),
                "tennis_breaks_home": safe_float_parse(row.get('tennis_breaks_home', 0)),
                "tennis_breaks_away": safe_float_parse(row.get('tennis_breaks_away', 0)),
            })
        
        # Гандбольные фичи
        if row.get('sport') == 'handball':
            feature_row.update({
                "handball_projected_total": float(row.get('handball_projected_total', 0)) if pd.notna(row.get('handball_projected_total')) else 0,
            })
        
        # Вычисляем разницы
        feature_row["score_diff"] = feature_row["score_home"] - feature_row["score_away"]
        if 'xg_diff' in feature_row:
            feature_row["xg_diff"] = feature_row.get("xg_home", 0) - feature_row.get("xg_away", 0)
        
        ml_features.append(feature_row)
    
    # Создаём DataFrame
    ml_df = pd.DataFrame(ml_features)
    
    # Сохраняем
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    ml_df.to_csv(output_file, index=False, encoding='utf-8')
    
    print(f"\n✅ ML датасет подготовлен: {len(ml_df)} записей")
    print(f"   Сохранён в: {output_file}")
    print(f"\n📊 Статистика по видам спорта:")
    if 'sport' in ml_df.columns:
        print(ml_df['sport'].value_counts().to_string())
    
    return ml_df

def main():
    """Основная функция"""
    print("=" * 60)
    print("ИСТОРИЧЕСКИЕ ДАННЫЕ ДЛЯ ML BASELINE")
    print("=" * 60)
    
    # 1. Проверяем sportsipy
    print("\n1️⃣ Проверка sportsipy...")
    capabilities = analyze_sportsipy_capabilities()
    
    if capabilities:
        print("\n📋 Возможности sportsipy:")
        print(f"   Виды спорта: {', '.join(capabilities['available_sports'])}")
        print(f"   Типы данных: {', '.join(capabilities['data_types'])}")
        print("\n⚠️  Ограничения:")
        for lim in capabilities['limitations']:
            print(f"   • {lim}")
    
    # 2. Загружаем live-логи
    print("\n2️⃣ Загрузка live-логов...")
    live_logs = load_live_logs()
    
    # 3. Подготавливаем ML датасет
    if not live_logs.empty:
        print("\n3️⃣ Подготовка ML датасета...")
        ml_dataset = prepare_ml_dataset(live_logs)
        
        if ml_dataset is not None and not ml_dataset.empty:
            print("\n✅ Готово! Датасет для ML baseline создан")
            print("\n📝 Следующие шаги:")
            print("   • Загрузить результаты матчей через update_results.py")
            print("   • Добавить целевые переменные (win/loss/push)")
            print("   • Построить baseline модели")
    else:
        print("\n⚠️  Нет live-логов для обработки")

if __name__ == "__main__":
    main()

