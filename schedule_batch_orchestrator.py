# -*- coding: utf-8 -*-
"""
Планировщик: периодический запуск пакетного пайплайна и проверки результатов ML

Правила:
- Рабочие часы берём из config.json
- Интервал запуска — parser_settings.interval_minutes
- Каждый цикл:
  1) Запускаем единичный батч-ран (MCP → батчи → Telegram → ML pending)
  2) Раз в N циклов запускаем обновление результатов ML (ml_result_checker)
"""
import json
import time
from datetime import datetime
from batch_run_now import main as run_once
from ml_result_checker import MLResultChecker


def within_hours(start_hm: str, end_hm: str) -> bool:
    now = datetime.now().strftime('%H:%M')
    return start_hm <= now <= end_hm


def main():
    with open('config.json', 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    interval_min = int(cfg['parser_settings']['interval_minutes'])
    start_h = cfg['parser_settings']['working_hours']['start']
    end_h = cfg['parser_settings']['working_hours']['end']

    ml_every = 2  # обновлять результаты ML примерно раз в 2 цикла
    cycle = 0

    print("=" * 60)
    print("🕒 Планировщик пакетного анализа запущен")
    print("=" * 60)

    while True:
        if within_hours(start_h, end_h):
            print(f"\n⏩ Старт цикла: {datetime.now().strftime('%H:%M:%S')}")
            try:
                run_once()
            except Exception as e:
                print(f"⚠️ Ошибка цикла анализатора: {e}")

            cycle += 1
            if cycle % ml_every == 0:
                try:
                    print("\n🔁 Обновление результатов ML (pending → won/lost)")
                    MLResultChecker().check_pending(min_age_minutes=90)
                except Exception as e:
                    print(f"⚠️ Ошибка обновления ML-результатов: {e}")
        else:
            print(f"⏳ Вне рабочих часов ({start_h}-{end_h}), ожидание...")

        time.sleep(interval_min * 60)


if __name__ == "__main__":
    main()


