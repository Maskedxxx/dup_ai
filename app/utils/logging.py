# app/utils/logging.py
from __future__ import annotations

import logging
import os
import time
import uuid
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

LOG_DIR = Path(__file__).resolve().parent.parent.parent / "LOGS"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Глобальные переменные для единого логгера
_unified_logger: Optional[logging.Logger] = None
_current_pipeline_id: Optional[str] = None


def _build_formatter() -> logging.Formatter:
    """
    Форматтер для логов.
    """
    fmt = (
        "%(asctime)s | %(levelname)s | "
        "%(name)s/%(filename)s:%(funcName)s:%(lineno)d | %(message)s"
    )
    return logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S")


def _get_unified_logger() -> logging.Logger:
    """
    Создает или возвращает единый логгер для всего приложения.
    """
    global _unified_logger
    
    if _unified_logger is not None:
        return _unified_logger
    
    # Создаем единый логгер для всего приложения
    _unified_logger = logging.getLogger("dup_ai")
    _unified_logger.setLevel(logging.DEBUG)
    
    # Если обработчики уже есть, не добавляем новые
    if _unified_logger.handlers:
        return _unified_logger
    
    formatter = _build_formatter()

    # ── терминал ────────────────────────────────────────────────────────────────
    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    sh.setFormatter(formatter)
    _unified_logger.addHandler(sh)

    # ── единый файл логов для всего приложения ──────────────────────────────────
    log_file = LOG_DIR / "dup_ai.log"
    fh = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding="utf-8",
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    _unified_logger.addHandler(fh)

    _unified_logger.propagate = False  # исключаем дублирование

    _unified_logger.info(f"Единый логгер инициализирован. Файл: {log_file}")
    return _unified_logger


def setup_logger(name: str, **kwargs) -> logging.Logger:
    """
    Возвращает единый логгер для всего приложения.
    Параметры name и kwargs игнорируются для обратной совместимости.
    
    :param name: имя логгера (игнорируется)
    :return: единый логгер приложения
    """
    # Всегда возвращаем единый логгер
    return _get_unified_logger()


class PipelineLogger:
    """
    Специальный логгер для пайплайнов с блочным логированием.
    """
    
    def __init__(self, logger_name: str):
        # Используем единый логгер вместо создания отдельного
        self.logger = _get_unified_logger()
        self.logger_name = logger_name
        self.pipeline_id: Optional[str] = None
        self.start_time: Optional[float] = None
        
    def start_pipeline_block(self, button_type: str, question: str) -> str:
        """
        Начинает блок логирования пайплайна.
        
        :param button_type: Тип кнопки (contractors, risks, etc.)
        :param question: Вопрос пользователя
        :return: ID пайплайна для связки логов
        """
        global _current_pipeline_id
        
        self.pipeline_id = str(uuid.uuid4())[:8]
        _current_pipeline_id = self.pipeline_id
        self.start_time = time.time()
        
        # Определяем режим логирования
        from app.config import app_settings
        log_mode = "DEBUG" if app_settings.debug else "PROD"
        
        separator = "=" * 80
        self.logger.info(f"\n{separator}")
        self.logger.info(f"[БЛОК НАЧАЛО] Pipeline ID: {self.pipeline_id} | Режим: {log_mode}")
        self.logger.info(f"[ЗАПРОС] Кнопка: {button_type} | Вопрос: '{question}'")
        self.logger.info(f"{separator}")
        
        return self.pipeline_id
    
    def end_pipeline_block(self, success: bool = True, error_msg: str = ""):
        """
        Завершает блок логирования пайплайна.
        
        :param success: Успешно ли завершился пайплайн
        :param error_msg: Сообщение об ошибке, если есть
        """
        global _current_pipeline_id
        
        if self.start_time:
            duration = time.time() - self.start_time
        else:
            duration = 0
            
        separator = "=" * 80
        
        if success:
            self.logger.info(f"[БЛОК КОНЕЦ] Pipeline ID: {self.pipeline_id} | Успешно завершен за {duration:.2f}с")
        else:
            self.logger.error(f"[БЛОК КОНЕЦ] Pipeline ID: {self.pipeline_id} | ОШИБКА за {duration:.2f}с: {error_msg}")
            
        self.logger.info(f"{separator}\n")
        
        _current_pipeline_id = None
        self.pipeline_id = None
        self.start_time = None
    
    def log_step_ok(self, step_num: int, step_name: str, details: str = ""):
        """
        Логирует успешное выполнение шага.
        
        :param step_num: Номер шага
        :param step_name: Название шага
        :param details: Дополнительные детали
        """
        from app.config import app_settings
        
        if app_settings.debug:
            # В режиме DEBUG показываем детали
            self.logger.info(f"[ШАГ {step_num} ОК] {step_name}: {details}")
        else:
            # В режиме PROD только статус
            self.logger.info(f"[ШАГ {step_num} ОК] {step_name}")
    
    def log_step_error(self, step_num: int, step_name: str, error_msg: str):
        """
        Логирует ошибку выполнения шага.
        
        :param step_num: Номер шага
        :param step_name: Название шага  
        :param error_msg: Сообщение об ошибке
        """
        self.logger.error(f"[ШАГ {step_num} ОШИБКА] {step_name}: {error_msg}")
    
    def log_detail(self, message: str, level: str = "INFO"):
        """
        Логирует детальную информацию (только в DEBUG режиме).
        
        :param message: Сообщение для логирования
        :param level: Уровень логирования (INFO, DEBUG, WARNING, ERROR)
        """
        from app.config import app_settings
        
        if not app_settings.debug:
            return  # В PROD режиме детали не логируем
            
        pipeline_prefix = f"[{self.pipeline_id}]" if self.pipeline_id else "[NO_PIPELINE]"
        full_message = f"{pipeline_prefix} {message}"
        
        if level.upper() == "DEBUG":
            self.logger.debug(full_message)
        elif level.upper() == "WARNING":
            self.logger.warning(full_message)
        elif level.upper() == "ERROR":
            self.logger.error(full_message)
        else:  # INFO
            self.logger.info(full_message)
    
    def log_prompt_details(self, prompt_type: str, system_prompt: str, user_prompt: str, response: str = ""):
        """
        Логирует детали промптов и ответов LLM.
        
        :param prompt_type: Тип промпта (classification, answer_generation)
        :param system_prompt: Системный промпт
        :param user_prompt: Пользовательский промпт
        :param response: Ответ от LLM
        """
        from app.config import app_settings
        
        if not app_settings.debug:
            return
            
        separator = "-" * 40
        self.log_detail(f"=== {prompt_type.upper()} ПРОМПТ ===")
        self.log_detail(f"{separator}")
        
        if system_prompt:
            self.log_detail(f"SYSTEM PROMPT:\n{system_prompt}")
            self.log_detail(f"{separator}")
            
        if user_prompt:
            self.log_detail(f"USER PROMPT:\n{user_prompt}")
        
        if response:
            self.log_detail(f"{separator}")
            self.log_detail(f"LLM RESPONSE:\n{response}")
            
        self.log_detail(f"=== END {prompt_type.upper()} ===")


# Функция для получения логгера пайплайна
def get_pipeline_logger(name: str) -> PipelineLogger:
    """
    Создает логгер пайплайна.
    
    :param name: Имя логгера
    :return: Экземпляр PipelineLogger
    """
    return PipelineLogger(name)