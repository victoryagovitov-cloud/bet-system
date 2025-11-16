#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Упаковка файлов для переноса на сервер
Создает ZIP архив с необходимыми файлами
"""

import os
import zipfile
from datetime import datetime

# Список файлов для переноса
CRITICAL_FILES = [
    'working_autoclicker.py',
    'send_fixed_analysis.py',
    'start_working_autoclicker.bat',
    'requirements.txt',
]

DOCUMENTATION_FILES = [
    'AUTONOMOUS_SYSTEM_GUIDE.md',
    'ALGORITHM_MATCH_SELECTION.md',
    'WORKING_METHOD.md',
    'FILES_TO_MIGRATE.txt',
]

OPTIONAL_FILES = [
    'AUTOMATION_INSTRUCTIONS.md',
    'CHANNEL_DEVELOPMENT_STRATEGY.md',
    'COMPLETE_DEVELOPMENT_ROADMAP.md',
    'COMPLETE_PROJECT_GUIDE.md',
    'FINAL_BALANCED_STRATEGY.md',
    'FINAL_PROJECT_DESCRIPTION.md',
    'FINAL_SETUP_INSTRUCTIONS.md',
    'MESSAGE_FORMAT_EXAMPLES.md',
    'MESSAGE_TEMPLATE_STANDARD.md',
    'MIGRATION_CHECKLIST.md',
    'PREMIUM_LAUNCH_CHECKLIST.md',
    'PREMIUM_STRATEGY_500_WEEK.md',
    'PROMOTION_STRATEGY.md',
    'QUICK_START_CHECKLIST.md',
    'README_SESSION_SUMMARY.md',
    'README_SETUP.md',
    'SCHEDULE_PLAN.md',
    'TENNIS_RULES_STRICT.md',
    'TIMEWEB_SETUP_GUIDE.md',
    'VISUAL_BRANDING_GUIDE.md',
]

def create_archive(include_optional=False):
    """Создать ZIP архив с файлами"""
    
    # Имя архива с датой
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    archive_name = f'betboom_analyzer_{timestamp}.zip'
    
    # Список файлов для упаковки
    files_to_pack = CRITICAL_FILES + DOCUMENTATION_FILES
    
    if include_optional:
        files_to_pack += OPTIONAL_FILES
    
    # Создание архива
    with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        packed_count = 0
        missing_count = 0
        
        print(f"📦 Создание архива: {archive_name}\n")
        
        for file in files_to_pack:
            if os.path.exists(file):
                zipf.write(file)
                print(f"✅ {file}")
                packed_count += 1
            else:
                print(f"⚠️  {file} - НЕ НАЙДЕН")
                missing_count += 1
        
        print(f"\n{'='*60}")
        print(f"📊 РЕЗУЛЬТАТ:")
        print(f"{'='*60}")
        print(f"✅ Упаковано файлов: {packed_count}")
        print(f"⚠️  Не найдено: {missing_count}")
        print(f"📦 Архив: {archive_name}")
        print(f"📏 Размер: {os.path.getsize(archive_name) / 1024:.2f} KB")
        print(f"{'='*60}\n")
        
        return archive_name

if __name__ == "__main__":
    print("═" * 60)
    print("📦 УПАКОВКА ФАЙЛОВ ДЛЯ МИГРАЦИИ НА СЕРВЕР")
    print("═" * 60)
    print("\nВыберите вариант:")
    print("1. Минимальный (8 файлов - только необходимое)")
    print("2. Полный (32 файла - с документацией)")
    print()
    
    choice = input("Введите 1 или 2: ").strip()
    
    include_optional = (choice == '2')
    
    print()
    archive_name = create_archive(include_optional)
    
    print("🎉 Готово!")
    print(f"\n📤 Перенесите файл {archive_name} на сервер")
    print("🔧 Распакуйте: unzip", archive_name)
    print("🚀 Следуйте инструкциям в SERVER_MIGRATION_GUIDE.md\n")

