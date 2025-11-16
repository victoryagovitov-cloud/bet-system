# -*- coding: utf-8 -*-
"""
Тест скорости загрузки Scores24 через MCP browser
"""
import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 70)
print("⏱️ ТЕСТ СКОРОСТИ SCORES24 ЧЕРЕЗ MCP BROWSER")
print("=" * 70)

# Записываем время начала
start_time = time.time()

print("\n🔄 Будет выполнено через MCP browser navigate...")
print(f"⏰ Старт: {time.strftime('%H:%M:%S')}\n")

# MCP browser не имеет настроек для отключения изображений/CSS
# Это нужно сделать в основном коде через tool call

print("📝 ПРИМЕЧАНИЕ:")
print("   MCP browser НЕ поддерживает:")
print("   ❌ Отключение изображений/CSS")
print("   ❌ Изменение pageLoadStrategy")
print("   ❌ Блокировку JS")
print("\n   ✅ MCP browser может только:")
print("   ✅ Навигация по URL")
print("   ✅ Базовое ожидание загрузки")
print("\n   Для оптимизации нужен SELENIUM!")
print("\n" + "=" * 70)
