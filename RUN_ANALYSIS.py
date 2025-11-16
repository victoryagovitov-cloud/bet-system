#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ГЛАВНЫЙ СКРИПТ - Запускается после сигнала 🎯F

Алгоритм:
1. Открывает BetBoom через Browser MCP
2. Получает snapshot (HTML)
3. Парсит и анализирует
4. Отправляет в @TrueLiveBет
"""

import sys
import os
if sys.platform == "win32":
    os.environ['PYTHONIOENCODING'] = 'utf-8'

sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path
from datetime import datetime

# ============================================================================
# ИНСТРУКЦИЯ
# ============================================================================

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                     🚀 ФИНАЛЬНАЯ АВТОНОМНАЯ СИСТЕМА                       ║
║                                                                            ║
║  Алгоритм работы после сигнала 🎯F:                                      ║
╚════════════════════════════════════════════════════════════════════════════╝

ШАГИ:

1️⃣ ОТКРЫТЬ BETBOOM (через Browser MCP)
   @mcp_cursor-browser-extension browser_navigate
   url: https://betboom.ru/sport/football?period=all&type=live

2️⃣ ПОДОЖДАТЬ ЗАГРУЗКИ (15 сек)
   @mcp_cursor-browser-extension browser_wait_for
   time: 15

3️⃣ ПОЛУЧИТЬ SNAPSHOT
   @mcp_cursor-browser-extension browser_snapshot

4️⃣ СКОПИРОВАТЬ HTML из результата

5️⃣ ЗАПУСТИТЬ АНАЛИЗ
   python RUN_ANALYSIS.py <HTML>

или прямо отправить HTML сюда:

""")

# ============================================================================
# ПОЛУЧЕНИЕ HTML ИЗ АРГУМЕНТОВ
# ============================================================================

def get_html_from_input():
    """Получает HTML из stdin"""
    
    print("📥 Ожидаю HTML от Browser MCP...\n")
    
    try:
        html = sys.stdin.read()
        
        if html and len(html) > 100:
            print(f"✅ Получен HTML ({len(html)} символов)\n")
            return html
        else:
            print("❌ HTML не получен или слишком короткий\n")
            return None
    
    except Exception as e:
        print(f"❌ Ошибка: {e}\n")
        return None


def main():
    """Главная функция"""
    
    print("=" * 80)
    print("🎯 ПОЛУЧЕН СИГНАЛ - НАЧИНАЮ АНАЛИЗ")
    print("=" * 80 + "\n")
    
    # Получаем HTML
    if len(sys.argv) > 1:
        # HTML передан как аргумент
        html = sys.argv[1]
    else:
        # HTML из stdin
        html = get_html_from_input()
    
    if not html:
        print("❌ HTML не найден\n")
        return False
    
    # Импортируем и запускаем анализ
    try:
        from final_autonomous_system import main as analyze
        
        print("🔵 Запускаю анализ...\n")
        success = analyze(html)
        
        return success
    
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}\n")
        print("Убедись что final_autonomous_system.py в той же папке\n")
        return False
    
    except Exception as e:
        print(f"❌ Ошибка: {e}\n")
        return False


if __name__ == '__main__':
    result = main()
    
    if result:
        print("\n✅ АНАЛИЗ ЗАВЕРШЕН!\n")
    else:
        print("\n❌ АНАЛИЗ ЗАВЕРШИЛСЯ С ОШИБКОЙ\n")

