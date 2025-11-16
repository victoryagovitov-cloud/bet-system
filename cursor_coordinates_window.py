# -*- coding: utf-8 -*-
"""
ОКНО ДЛЯ ОПРЕДЕЛЕНИЯ КООРДИНАТ КУРСОРА
Показывает координаты мыши в реальном времени
"""
import sys
import io
import tkinter as tk
from tkinter import font
import pyautogui
import time

# Настройка UTF-8 для вывода
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class CoordinatesWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Координаты курсора")
        self.root.geometry("400x200")
        self.root.attributes('-topmost', True)  # Поверх всех окон
        
        # Настройка шрифтов
        self.big_font = font.Font(family="Arial", size=16, weight="bold")
        self.small_font = font.Font(family="Arial", size=12)
        
        # Заголовок
        title_label = tk.Label(
            root, 
            text="КООРДИНАТЫ КУРСОРА",
            font=self.big_font,
            fg="blue"
        )
        title_label.pack(pady=10)
        
        # Поле для X
        x_frame = tk.Frame(root)
        x_frame.pack(pady=5)
        tk.Label(x_frame, text="X:", font=self.small_font, width=5).pack(side=tk.LEFT)
        self.x_label = tk.Label(
            x_frame, 
            text="0", 
            font=self.big_font,
            bg="white",
            width=10,
            relief=tk.SUNKEN
        )
        self.x_label.pack(side=tk.LEFT, padx=5)
        
        # Поле для Y
        y_frame = tk.Frame(root)
        y_frame.pack(pady=5)
        tk.Label(y_frame, text="Y:", font=self.small_font, width=5).pack(side=tk.LEFT)
        self.y_label = tk.Label(
            y_frame, 
            text="0", 
            font=self.big_font,
            bg="white",
            width=10,
            relief=tk.SUNKEN
        )
        self.y_label.pack(side=tk.LEFT, padx=5)
        
        # Кнопка копирования
        copy_frame = tk.Frame(root)
        copy_frame.pack(pady=10)
        
        self.copy_button = tk.Button(
            copy_frame,
            text="Копировать координаты",
            command=self.copy_coordinates,
            bg="#4CAF50",
            fg="white",
            font=self.small_font,
            padx=10,
            pady=5
        )
        self.copy_button.pack()
        
        # Инструкция
        info_label = tk.Label(
            root,
            text="Наведите мышь на поле ввода чата Cursor",
            font=font.Font(family="Arial", size=9),
            fg="gray"
        )
        info_label.pack(pady=5)
        
        # Запуск обновления координат
        self.update_coordinates()
        
    def update_coordinates(self):
        """Обновляет координаты каждые 100мс"""
        x, y = pyautogui.position()
        self.x_label.config(text=str(x))
        self.y_label.config(text=str(y))
        self.root.after(100, self.update_coordinates)  # Обновление каждые 100мс
        
    def copy_coordinates(self):
        """Копирует координаты в буфер обмена"""
        x, y = pyautogui.position()
        coordinates = f"{x}, {y}"
        self.root.clipboard_clear()
        self.root.clipboard_append(coordinates)
        
        # Временная метка успеха
        old_text = self.copy_button.cget("text")
        self.copy_button.config(text="✓ Скопировано!", bg="#2E7D32")
        self.root.after(1500, lambda: self.copy_button.config(text=old_text, bg="#4CAF50"))

def main():
    print("=" * 70)
    print("ОКНО КООРДИНАТ КУРСОРА")
    print("=" * 70)
    print()
    print("Инструкция:")
    print("1. Откроется окно с координатами мыши")
    print("2. Наведи мышь на поле ввода чата Cursor")
    print("3. Скопируй координаты кнопкой")
    print("4. Вставь в cursor_autosend.ahk")
    print()
    print("Окно показывается поверх всех окон")
    print()
    
    root = tk.Tk()
    app = CoordinatesWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()

