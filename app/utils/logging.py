# app/utils/logging.py
from __future__ import annotations

import logging
import os
import time
import uuid
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional
from contextvars import ContextVar

LOG_DIR = Path(__file__).resolve().parent.parent.parent / "LOGS"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Глобальные переменные для единого логгера
_unified_logger: Optional[logging.Logger] = None
_summary_logger: Optional[logging.Logger] = None
_current_pipeline_id_var: ContextVar[Optional[str]] = ContextVar("pipeline_id", default=None)


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


def _get_summary_logger() -> logging.Logger:
    """
    Создает или возвращает отдельный логгер для краткого саммари.
    Пишет только ключевые события пайплайна: START, STEP_OK, ANSWER, END.
    """
    global _summary_logger

    if _summary_logger is not None:
        return _summary_logger

    _summary_logger = logging.getLogger("dup_ai_summary")
    _summary_logger.setLevel(logging.INFO)

    # Если обработчики уже есть, не добавляем новые
    if _summary_logger.handlers:
        return _summary_logger

    # Формат для саммари с поддержкой pipeline_id и шага
    fmt = "%(asctime)s | %(levelname)s | pipeline=%(pipeline_id)s | %(message)s"
    formatter = logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S")

    # Файл логов для саммари
    summary_file = LOG_DIR / "dup_ai_summary.log"
    fh = RotatingFileHandler(
        summary_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding="utf-8",
    )
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    _summary_logger.addHandler(fh)

    _summary_logger.propagate = False

    return _summary_logger


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
        # Отдельный логгер для саммари
        self.summary = _get_summary_logger()
        self.logger_name = logger_name
        self.pipeline_id: Optional[str] = None
        self.start_time: Optional[float] = None
        
    @staticmethod
    def _short(text: Optional[str], limit: int = 160) -> str:
        if not text:
            return ""
        t = str(text).replace("\n", " ")
        return t if len(t) <= limit else (t[:limit] + "...")
        
    def start_pipeline_block(self, button_type: str, question: str) -> str:
        """
        Начинает блок логирования пайплайна.
        
        :param button_type: Тип кнопки (contractors, risks, etc.)
        :param question: Вопрос пользователя
        :return: ID пайплайна для связки логов
        """
        self.pipeline_id = str(uuid.uuid4())[:8]
        # Сохраняем токен, чтобы уметь сбрасывать значение позже
        self._pipeline_token = _current_pipeline_id_var.set(self.pipeline_id)
        self.start_time = time.time()
        
        # Определяем режим логирования
        from app.config import app_settings
        log_mode = "DEBUG" if app_settings.debug else "PROD"
        
        separator = "=" * 80
        self.logger.info(f"\n{separator}")
        self.logger.info(f"[БЛОК НАЧАЛО] Pipeline ID: {self.pipeline_id} | Режим: {log_mode}")
        self.logger.info(f"[ЗАПРОС] Кнопка: {button_type} | Вопрос: '{question}'")
        self.logger.info(f"{separator}")
        
        # В саммари пишем START с полным вопросом
        self.summary.info(
            f"START | button={button_type} | question={question}",
            extra={"pipeline_id": self.pipeline_id}
        )
        
        return self.pipeline_id
    
    def end_pipeline_block(self, success: bool = True, error_msg: str = ""):
        """
        Завершает блок логирования пайплайна.
        
        :param success: Успешно ли завершился пайплайн
        :param error_msg: Сообщение об ошибке, если есть
        """
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
        
        # В саммари пишем END
        self.summary.info(
            f"END | success={success} | duration={duration:.2f}s",
            extra={"pipeline_id": self.pipeline_id}
        )
        
        # Сбрасываем контекстный pipeline_id
        try:
            _current_pipeline_id_var.reset(self._pipeline_token)  # вернуть предыдущее значение
        except Exception:
            _current_pipeline_id_var.set(None)
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
        
        # В саммари всегда пишем краткую запись шага
        current_id = self.pipeline_id or _current_pipeline_id_var.get()
        summary_details = details if details else ""
        self.summary.info(
            f"STEP_OK | step={step_num} {step_name} | {self._short(summary_details)}",
            extra={"pipeline_id": current_id}
        )
    
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
            
        # Используем глобальный pipeline_id если локальный не установлен
        current_id = self.pipeline_id or _current_pipeline_id_var.get()
        
        pipeline_prefix = f"[{current_id}]" if current_id else "[NO_PIPELINE]"
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

    def log_answer_summary(self, text: str, total_found: int):
        """
        Пишет короткое резюме ответа в саммари-лог (обрезанный текст ответа).
        Вопрос полностью уже записан в START.
        """
        current_id = self.pipeline_id or _current_pipeline_id_var.get()
        self.summary.info(
            f"ANSWER | total={total_found} | {self._short(text)}",
            extra={"pipeline_id": current_id}
        )


# Функция для получения логгера пайплайна
def get_pipeline_logger(name: str) -> PipelineLogger:
    """
    Создает логгер пайплайна.
    
    :param name: Имя логгера
    :return: Экземпляр PipelineLogger
    """
    return PipelineLogger(name)
