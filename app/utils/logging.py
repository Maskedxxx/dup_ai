# app/utils/logging.py
from __future__ import annotations

import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

# Единый файл логов для всей системы
GLOBAL_LOG_FILE = "pipeline.log"
_global_handler: Optional[RotatingFileHandler] = None

LOG_DIR = Path(__file__).resolve().parent.parent.parent / "LOGS"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def _build_formatter() -> logging.Formatter:
    """
    2025‑05‑06 12:51:52 | INFO | app.services.normalization/normalization.py:clean_df:20 | Сообщение
                        │      │                       │               │        │
                        │      │                       │               │        └─ № строки
                        │      │                       │               └─ функция
                        │      │                       └─ имя файла (.py)
                        │      └─ пакет/модуль (logger.name)
                        └─ уровень
    """
    fmt = (
        "%(asctime)s | %(levelname)s | "
        "%(name)s/%(filename)s:%(funcName)s:%(lineno)d | %(message)s"
    )
    return logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S")


def setup_logger(
    name: str,
    stream_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 3,
) -> logging.Logger:
    """
    Логгер с двумя обработчиками и единым файлом логов:
    • StreamHandler  – в терминал (>= INFO)
    • RotatingFileHandler – в LOGS/<name>.log (>= DEBUG)
    • RotatingFileHandler – в LOGS/pipeline.log (>= DEBUG) для общей трассировки

    :param name: имя логгера (обычно __name__)
    """
    logger = logging.getLogger(name)
    logger.setLevel(min(stream_level, file_level))

    if logger.handlers:                       # повторная инициализация не нужна
        return logger

    formatter = _build_formatter()

    # ── терминал ────────────────────────────────────────────────────────────────
    sh = logging.StreamHandler()
    sh.setLevel(stream_level)
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    # ── файл с ротацией ────────────────────────────────────────────────────────
    log_file = LOG_DIR / f"{name}.log"
    fh = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    fh.setLevel(file_level)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    global _global_handler
    if _global_handler is None:
        global_log_file = LOG_DIR / GLOBAL_LOG_FILE
        _global_handler = RotatingFileHandler(
            global_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        _global_handler.setLevel(file_level)
        _global_handler.setFormatter(formatter)

    logger.addHandler(_global_handler)

    logger.propagate = False                 # исключаем дублирование

    logger.debug(
        "Логгер «%s» инициализирован. Файлы: %s и %s (rotate @ %d bytes, keep %d).",
        name,
        log_file,
        GLOBAL_LOG_FILE,
        max_bytes,
        backup_count,
    )
    return logger
