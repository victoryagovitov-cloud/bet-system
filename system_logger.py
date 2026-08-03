#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Централизованная система логирования для всей системы.
Заменяет все print на структурированное логирование.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional
import json

TZ_MOSCOW = ZoneInfo("Europe/Moscow")
DATA_DIR = Path("data")
LOGS_DIR = DATA_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Файлы логов
MAIN_LOG_FILE = LOGS_DIR / "system.log"
ERROR_LOG_FILE = LOGS_DIR / "errors.log"
DEBUG_LOG_FILE = LOGS_DIR / "debug.log"

# Формат логов
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Структурированный формат для JSON логов
JSON_LOG_FORMAT = {
    "timestamp": "%(asctime)s",
    "level": "%(levelname)s",
    "module": "%(name)s",
    "message": "%(message)s",
    "function": "%(funcName)s",
    "line": "%(lineno)d"
}


class StructuredFormatter(logging.Formatter):
    """Форматтер для структурированного логирования"""
    
    def format(self, record):
        # Добавляем время в московском часовом поясе
        record.asctime = datetime.now(TZ_MOSCOW).strftime(DATE_FORMAT)
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """JSON форматтер для структурированного логирования"""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.now(TZ_MOSCOW).isoformat(),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Добавляем exception info если есть
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Добавляем дополнительные поля
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data
        
        return json.dumps(log_data, ensure_ascii=False)


class SystemLogger:
    """Централизованный логгер системы"""
    
    _instance: Optional['SystemLogger'] = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.logger = logging.getLogger("system")
        self.logger.setLevel(logging.DEBUG)
        
        # Убираем дублирование логов
        self.logger.propagate = False
        
        # Очищаем существующие handlers
        self.logger.handlers.clear()
        
        # Консольный handler (INFO и выше)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = StructuredFormatter(LOG_FORMAT, DATE_FORMAT)
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # Файл для всех логов (DEBUG и выше)
        file_handler = logging.FileHandler(MAIN_LOG_FILE, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = StructuredFormatter(LOG_FORMAT, DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Файл только для ошибок (ERROR и выше)
        error_handler = logging.FileHandler(ERROR_LOG_FILE, encoding="utf-8")
        error_handler.setLevel(logging.ERROR)
        error_formatter = StructuredFormatter(LOG_FORMAT, DATE_FORMAT)
        error_handler.setFormatter(error_formatter)
        self.logger.addHandler(error_handler)
        
        # JSON лог для анализа (опционально)
        json_handler = logging.FileHandler(LOGS_DIR / "system.jsonl", encoding="utf-8")
        json_handler.setLevel(logging.INFO)
        json_formatter = JSONFormatter()
        json_handler.setFormatter(json_formatter)
        self.logger.addHandler(json_handler)
        
        # Ротация логов (если файл больше 10MB, создаем новый)
        self._setup_log_rotation()
        
        self._initialized = True
    
    def _setup_log_rotation(self):
        """Настраивает ротацию логов"""
        # Простая ротация: если файл больше 10MB, переименовываем
        max_size = 10 * 1024 * 1024  # 10MB
        
        for log_file in [MAIN_LOG_FILE, ERROR_LOG_FILE]:
            try:
                if log_file.exists() and log_file.stat().st_size > max_size:
                    # Переименовываем старый файл
                    backup_name = log_file.with_suffix(f".{datetime.now(TZ_MOSCOW).strftime('%Y%m%d_%H%M%S')}.log")
                    try:
                        log_file.rename(backup_name)
                    except (PermissionError, OSError) as e:
                        # Файл заблокирован другим процессом - пропускаем ротацию
                        # Это не критично, система продолжит работать
                        print(f"WARNING: Cannot rotate log file {log_file}: {e}. Continuing without rotation.", file=sys.stderr)
            except Exception as e:
                # Любая другая ошибка при проверке размера - игнорируем
                print(f"WARNING: Error checking log file {log_file}: {e}. Continuing.", file=sys.stderr)
    
    def debug(self, message: str, **kwargs):
        """Логирует DEBUG сообщение"""
        self.logger.debug(message, extra={"extra_data": kwargs} if kwargs else None)
    
    def info(self, message: str, **kwargs):
        """Логирует INFO сообщение"""
        self.logger.info(message, extra={"extra_data": kwargs} if kwargs else None)
    
    def warning(self, message: str, **kwargs):
        """Логирует WARNING сообщение"""
        self.logger.warning(message, extra={"extra_data": kwargs} if kwargs else None)
    
    def error(self, message: str, exc_info=None, **kwargs):
        """Логирует ERROR сообщение"""
        self.logger.error(message, exc_info=exc_info, extra={"extra_data": kwargs} if kwargs else None)
    
    def critical(self, message: str, exc_info=None, **kwargs):
        """Логирует CRITICAL сообщение"""
        self.logger.critical(message, exc_info=exc_info, extra={"extra_data": kwargs} if kwargs else None)
    
    def exception(self, message: str, **kwargs):
        """Логирует исключение с traceback"""
        self.logger.exception(message, extra={"extra_data": kwargs} if kwargs else None)


# Глобальный экземпляр
_logger_instance: Optional[SystemLogger] = None


def get_logger() -> SystemLogger:
    """Возвращает глобальный экземпляр логгера"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = SystemLogger()
    return _logger_instance


# Удобные функции для быстрого доступа
def log_debug(message: str, **kwargs):
    """Быстрый доступ к DEBUG логу"""
    get_logger().debug(message, **kwargs)


def log_info(message: str, **kwargs):
    """Быстрый доступ к INFO логу"""
    get_logger().info(message, **kwargs)


def log_warning(message: str, **kwargs):
    """Быстрый доступ к WARNING логу"""
    get_logger().warning(message, **kwargs)


def log_error(message: str, exc_info=None, **kwargs):
    """Быстрый доступ к ERROR логу"""
    get_logger().error(message, exc_info=exc_info, **kwargs)


def log_critical(message: str, exc_info=None, **kwargs):
    """Быстрый доступ к CRITICAL логу"""
    get_logger().critical(message, exc_info=exc_info, **kwargs)


def log_exception(message: str, **kwargs):
    """Быстрый доступ к логу исключения"""
    get_logger().exception(message, **kwargs)

