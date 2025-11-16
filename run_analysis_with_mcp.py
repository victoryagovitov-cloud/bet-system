#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Запуск анализа BetBoom с MCP Browser функциями из контекста Cursor
"""
from correct_analyzer_with_prefilter import main
import sys

# Импортируем MCP Browser функции из Cursor
# В контексте Cursor эти функции доступны через MCP инструменты

if __name__ == "__main__":
    # В контексте Cursor MCP Browser функции должны быть переданы
    # Но так как мы запускаем из Python напрямую, они недоступны
    # Поэтому вызываем main() без параметров - он проверит наличие функций
    print("Запуск анализа BetBoom с проверкой MCP Browser...")
    main()
