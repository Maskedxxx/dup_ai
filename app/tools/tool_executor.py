# app/tools/tool_executor.py

import json
import pandas as pd
from typing import Tuple, Dict
from app.adapters.llm_client import LLMClient
from app.tools.registry import tool_registry, ToolRegistry
from app.services.keybert_service import get_keybert_service
from app.utils.logging import setup_logger

# Настройка логгера
logger = setup_logger(__name__)


class ToolExecutor:
    """
    Выбирает и выполняет наиболее подходящий инструмент на основе запроса пользователя.
    """
    
    def __init__(self, llm_client: LLMClient, registry: ToolRegistry = tool_registry):
        """
        Инициализация исполнителя.
        
        :param llm_client: Клиент для взаимодействия с LLM.
        :param registry: Реестр инструментов.
        """
        self.llm_client = llm_client
        self.registry = registry
        self.keybert_service = get_keybert_service()
    
    def select_and_execute(self, question: str, df: pd.DataFrame, **kwargs) -> Tuple[pd.DataFrame, Dict[int, float]]:
        """
        1. Использует KeyBERT для извлечения ключевых слов из вопроса.
        2. Автоматически выбирает инструмент search_by_keywords.
        3. Выполняет поиск с извлеченными ключевыми словами.
        
        :param question: Вопрос пользователя.
        :param df: DataFrame для обработки.
        :param kwargs: Дополнительные аргументы для системного промпта.
        :return: Кортеж (Отфильтрованный DataFrame, Словарь с оценками релевантности).
        """
        try:
            logger.info(f"Извлечение ключевых слов из вопроса: '{question}'")
            
            # Используем KeyBERT для извлечения ключевых слов
            keywords = self._extract_keywords_with_keybert(question)
            
            if not keywords:
                logger.warning("KeyBERT не извлек ключевые слова. Возвращаем исходные данные.")
                return df, {}
            
            logger.info(f"KeyBERT извлек ключевые слова: {keywords}")
            
            # Автоматически выбираем search_by_keywords инструмент
            tool_name = "search_by_keywords"
            tool_to_execute = self.registry.get_tool(tool_name)
            
            if not tool_to_execute:
                logger.error(f"Инструмент '{tool_name}' не найден в реестре.")
                return df, {}
            
            # Подготавливаем аргументы с извлеченными ключевыми словами
            arguments = {
                'df': df,
                'keywords': keywords,
                'top_n': kwargs.get('top_n', 5)  # Используем top_n из kwargs или по умолчанию 5
            }
            
            logger.info(f"Выполняем инструмент '{tool_name}' с ключевыми словами: {keywords}")
            
            return tool_to_execute.execute(**arguments)
            
        except Exception as e:
            logger.error(f"Ошибка при выполнении KeyBERT инструмента: {e}", exc_info=True)
            return df, {}

    def _extract_keywords_with_keybert(self, question: str, top_n: int = 7) -> list:
        """
        Извлекает ключевые слова из вопроса с помощью KeyBERT.
        
        :param question: Вопрос пользователя
        :param top_n: Количество ключевых слов для извлечения
        :return: Список ключевых слов
        """
        try:
            keywords = self.keybert_service.extract_keywords(
                text=question,
                top_n=top_n,
                keyphrase_ngram_range=(1, 1)  # Только отдельные слова, не фразы
            )
            
            return keywords
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении ключевых слов с KeyBERT: {e}")
            return []

    def select_and_execute_legacy(self, question: str, df: pd.DataFrame, **kwargs) -> Tuple[pd.DataFrame, Dict[int, float]]:
        """
        LEGACY: Старая логика с использованием LLM для выбора инструментов.
        Оставлена для обратной совместимости.
        
        1. Получает схемы всех инструментов из реестра.
        2. Просит LLM выбрать наиболее подходящий инструмент и извлечь аргументы.
        3. Выполняет выбранный инструмент с извлеченными аргументами.
        
        :param question: Вопрос пользователя.
        :param df: DataFrame для обработки.
        :param kwargs: Дополнительные аргументы для системного промпта.
        :return: Кортеж (Отфильтрованный DataFrame, Словарь с оценками релевантности).
        """
        all_schemas = self.registry.get_all_schemas()
        
        if not all_schemas:
            logger.warning("В реестре нет доступных инструментов. Пропускаем выполнение.")
            return df, {}

        system_prompt = self._build_system_prompt(**kwargs)

        try:
            logger.info(f"Выбор инструмента для вопроса: '{question}'")
            
            response = self.llm_client.chat_completion_with_tools(
                system_prompt=system_prompt,
                user_prompt=f"Вопрос: {question}",
                tools=all_schemas,
                tool_choice="auto"  # Позволяем LLM выбирать инструмент
            )
            
            tool_calls = response.choices[0].message.tool_calls
            if not tool_calls:
                logger.warning("LLM не выбрал ни одного инструмента. Возвращаем исходные данные.")
                return df, {}

            # Берем первый вызов инструмента
            tool_call = tool_calls[0]
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            
            logger.info(f"LLM выбрал инструмент: '{tool_name}' с аргументами: {arguments}")
            
            # Находим и выполняем инструмент
            tool_to_execute = self.registry.get_tool(tool_name)
            if not tool_to_execute:
                logger.error(f"Выбранный LLM инструмент '{tool_name}' не найден в реестре.")
                return df, {}
            
            # Добавляем DataFrame в аргументы и выполняем
            arguments['df'] = df
            return tool_to_execute.execute(**arguments)
            
        except Exception as e:
            logger.error(f"Ошибка при выборе или выполнении инструмента: {e}", exc_info=True)
            return df, {}

    def _build_system_prompt(self, **kwargs) -> str:
        """
        Создает системный промпт на основе переданных данных.
        """
        # Пример: можно передавать project_name, category и т.д.
        # для более точного промпта.
        context = " ".join([f"{k}: {v}" for k, v in kwargs.items()])
        base_prompt = "Ты — эксперт по анализу данных. Твоя задача — на основе вопроса пользователя выбрать наиболее подходящий инструмент и извлечь из вопроса аргументы для его выполнения."
        return f"{base_prompt} Контекст запроса: {context}".strip()
