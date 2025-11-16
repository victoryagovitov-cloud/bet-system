#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

import glob
from pathlib import Path
from final_autonomous_system import main

# Берем самый свежий snapshot от Browser MCP
snapshots = sorted(
    glob.glob(r'c:\Users\Мария\.cursor\projects\d-cursor-Backtothestart-09-11-2025\agent-tools\*.txt'),
    key=os.path.getmtime,
    reverse=True
)

if snapshots:
    html_file = snapshots[0]
    print(f'\n📥 Загружаю snapshot: {Path(html_file).name}')
    
    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()
    
    print(f'✅ Готов к анализу ({len(html)} символов)\n')
    
    # Запускаем анализ
    main(html)
else:
    print('\n❌ Snapshot не найден\n')

