# -*- coding: utf-8 -*-
"""
Единичный запуск: BetBoom (MCP) → префильтр → параллельная проверка → батчи по 4 → Telegram → ML
"""
import sys
import io
from betboom_mcp_connector import get_betboom_matches_mcp
from batch_live_orchestrator import run_batch_pipeline


def main():
    # Перевязываем stdout на системный stdout на случай, если кто-то его закрыл/переназначил
    try:
        sys.stdout = io.TextIOWrapper(sys.__stdout__.buffer, encoding='utf-8', write_through=True)
    except Exception:
        pass

    all_matches = get_betboom_matches_mcp()
    # Стартуем батч-пайплайн (по 4)
    run_batch_pipeline(all_matches, batch_size=4)


if __name__ == "__main__":
    main()


