#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path
from final_autonomous_system import main

# Путь к файлу HTML от Browser MCP
html_file = Path(r'c:\Users\Мария\.cursor\projects\d-cursor-Backtothestart-09-11-2025\agent-tools\59ee6148-770c-4028-87f9-d84aabd53b21.txt')

if html_file.exists():
    print(f"\n✅ Загружаю HTML ({html_file.stat().st_size} байт)...\n")
    
    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()
    
    print(f"✅ HTML загружен ({len(html)} символов)\n")
    
    # Запускаем анализ
    main(html)
else:
    print(f"\n❌ Файл HTML не найден: {html_file}\n")

