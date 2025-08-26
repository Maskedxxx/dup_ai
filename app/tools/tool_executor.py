# app/tools/tool_executor.py

import json
import pandas as pd
from typing import Tuple, Dict
from app.adapters.llm_client import LLMClient
from app.tools.registry import tool_registry, ToolRegistry
from app.services.keybert_service import get_keybert_service
from app.utils.logging import setup_logger
from app.config import smart_filtering_settings
from app.domain.enums import ButtonType

# Настройка логгера
logger = setup_logger(__name__)

class ToolExecutor:
    """
    Оркестратор этапа "Умной Фильтрации".
    Выбирает и выполняет стратегию фильтрации (KeyBERT, LLM, etc.)
    на основе конфигурации для конкретного пайплайна.
    """
    
    def __init__(self, llm_client: LLMClient, registry: ToolRegistry = tool_registry):
        self.llm_client = llm_client
        self.registry = registry
        self.keybert_service = get_keybert_service()

    def apply_smart_filtering(self, question: str, df: pd.DataFrame, button_type: ButtonType, **kwargs) -> Tuple[pd.DataFrame, Dict[int, float]]:
        """
        Главный метод-оркестратор для этапа умной фильтрации.
        
        :param question: Вопрос пользователя.
        :param df: DataFrame для обработки.
        :param button_type: Тип пайплайна (кнопки).
        :param kwargs: Дополнительные аргументы.
        :return: Кортеж (Отфильтрованный DataFrame, Словарь с оценками релевантности).
        """
        strategy = smart_filtering_settings.strategy.get(button_type.value, "none")
        logger.info(f"Для пайплайна '{button_type.value}' выбрана стратегия умной фильтрации: '{strategy}'")

        if strategy == "keybert":
            return self._execute_keybert_strategy(question, df, **kwargs)
        elif strategy == "llm":
            return self._execute_llm_strategy(question, df, button_type, **kwargs)
        elif strategy == "both":
            return self._execute_combined_strategy(question, df, button_type, **kwargs)
        else: # "none"
            logger.info("Стратегия 'none', умная фильтрация не применяется.")
            return df, {}

    def _execute_keybert_strategy(self, question: str, df: pd.DataFrame, **kwargs) -> Tuple[pd.DataFrame, Dict[int, float]]:
        """
        Выполняет фильтрацию с использованием KeyBERT для извлечения ключевых слов.
        """
        try:
            # Получаем имя инструмента из конфига, а не жестко его кодируем
            tool_name = smart_filtering_settings.strategy_tool_map.get("keybert")
            if not tool_name:
                logger.error("В конфигурации не найдено имя инструмента для стратегии 'keybert'.")
                return df, {}

            logger.info(f"Запуск стратегии KeyBERT с инструментом '{tool_name}'")

            # Прямой вызов сервиса вместо дублирования
            keywords = self.keybert_service.extract_keywords(
                text=question,
                top_n=7,
                keyphrase_ngram_range=(1, 1)
            )
            if not keywords:
                logger.warning("KeyBERT не извлек ключевые слова. Возвращаем исходные данные.")
                return df, {}
            
            logger.info(f"KeyBERT извлек ключевые слова: {keywords}")

            tool_to_execute = self.registry.get_tool(tool_name)
            if not tool_to_execute:
                logger.error(f"Инструмент '{tool_name}', указанный в конфиге, не найден в реестре.")
                return df, {}

            arguments = {
                'df': df,
                'keywords': keywords,
                'top_n': kwargs.get('top_n', 5)
            }
            
            return tool_to_execute.execute(**arguments)

        except Exception as e:
            logger.error(f"Ошибка при выполнении стратегии KeyBERT: {e}", exc_info=True)
            return df, {}

    def _execute_llm_strategy(self, question: str, df: pd.DataFrame, button_type: ButtonType, **kwargs) -> Tuple[pd.DataFrame, Dict[int, float]]:
        """
        (ЗАГЛУШКА) Выполняет фильтрацию с использованием LLM для выбора инструментов.
        """
        logger.warning("Стратегия 'llm' еще не реализована. Возвращаем исходные данные.")
        # TODO: Реализовать логику:
        # 1. Загрузить схемы для button_type из `llm_schemas_path`
        # 2. Вызвать self.llm_client.chat_completion_with_tools
        # 3. Получить tool_call и выполнить инструмент из self.registry
        return df, {}

    def _execute_combined_strategy(self, question: str, df: pd.DataFrame, button_type: ButtonType, **kwargs) -> Tuple[pd.DataFrame, Dict[int, float]]:
        """
        (ЗАГЛУШКА) Выполняет обе стратегии и объединяет результаты.
        """
        logger.warning("Стратегия 'both' еще не реализована. Возвращаем исходные данные.")
        # TODO: Реализовать логику:
        # 1. Вызвать _execute_keybert_strategy
        # 2. Вызвать _execute_llm_strategy
        # 3. Объединить результаты (например, по пересечению или объединению)
        return df, {}

