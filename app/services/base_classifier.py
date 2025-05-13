# app/services/base_classifier.py

import pandas as pd
from typing import Dict, List, Tuple
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from app.adapters.llm_client import LLMClient
from app.utils.logging import setup_logger

# Настройка логгера
logger = setup_logger(__name__)


class ClassificationResult(BaseModel):
    """Результат классификации запроса."""
    reasoning: str = Field(..., description="Краткое рассуждение о классификации")
    top_items: Dict[str, float] = Field(..., description="Топ-3 элемента с оценками релевантности (от 0 до 1)")


class BaseClassifierService(ABC):
    """
    Базовый класс для всех сервисов классификации.
    Предоставляет общую логику для классификации запросов.
    """
    
    def __init__(self, llm_client: LLMClient):
        """
        Инициализация сервиса классификации.
        
        :param llm_client: Клиент для взаимодействия с LLM
        """
        self.llm_client = llm_client
        self.items_list: List[str] = []
        logger.info(f"Инициализирован {self.__class__.__name__}")
    
    @abstractmethod
    def get_column_name(self) -> str:
        """
        Возвращает название колонки для извлечения элементов.
        Должен быть реализован в наследниках.
        
        :return: Название колонки в DataFrame
        """
        pass
    
    @abstractmethod
    def get_item_type(self) -> str:
        """
        Возвращает тип элементов для использования в промптах.
        Должен быть реализован в наследниках.
        
        :return: Тип элементов (например, "проект", "процесс")
        """
        pass
    
    def load_items(self, df: pd.DataFrame) -> List[str]:
        """
        Загружает список уникальных элементов из DataFrame.
        
        :param df: DataFrame с данными
        :return: Список уникальных элементов
        """
        column_name = self.get_column_name()
        
        try:
            if column_name in df.columns:
                # Фильтруем пустые значения и преобразуем в список
                unique_items = df[column_name].dropna().unique().tolist()
                
                # Фильтруем пустые строки
                unique_items = [item for item in unique_items if item and isinstance(item, str)]
                
                logger.info(f"Загружено {len(unique_items)} уникальных элементов из колонки '{column_name}'")
                self.items_list = unique_items
                return unique_items
            else:
                logger.warning(f"Колонка '{column_name}' не найдена в данных")
                return []
        except Exception as e:
            logger.error(f"Ошибка при загрузке элементов: {e}")
            return []
    
    def classify(self, question: str) -> str:
        """
        Классифицирует вопрос пользователя и определяет наиболее релевантный элемент.
        
        :param question: Вопрос пользователя
        :return: Наиболее релевантный элемент
        """
        logger.info(f"Классификация запроса: '{question}'")
        
        if not self.items_list:
            logger.warning("Список элементов пуст, невозможно классифицировать запрос")
            return ""
        
        # Получаем промпты для классификации
        prompts = self._build_classification_prompts(question)
        
        try:
            # Вызываем API для структурированного ответа
            result = self.llm_client.generate_structured_completion(
                system_prompt=prompts['system'],
                user_prompt=prompts['user'],
                response_model=ClassificationResult,
                temperature=0
            )
            
            if result and hasattr(result, 'top_items'):
                top_items = result.top_items
                logger.info(f"Рассуждение модели: {result.reasoning}")
                logger.info(f"Топ-3 элемента: {top_items}")
                
                # Находим элемент с наивысшей оценкой
                if top_items:
                    best_item = max(top_items.items(), key=lambda x: x[1])
                    logger.info(f"Выбран элемент: {best_item[0]} с оценкой {best_item[1]}")
                    
                    return best_item[0]
            
            logger.warning("Модель не вернула структурированный ответ")
            return ""
                
        except Exception as e:
            logger.error(f"Ошибка при классификации запроса: {e}")
            return ""
    
    def filter_items(self, df: pd.DataFrame, item_value: str) -> Tuple[pd.DataFrame, Dict[int, float]]:
        """
        Фильтрует DataFrame по значению элемента.
        
        :param df: DataFrame с данными
        :param item_value: Значение для фильтрации
        :return: Кортеж из отфильтрованного DataFrame и словаря оценок
        """
        column_name = self.get_column_name()
        logger.info(f"Фильтрация по колонке '{column_name}' со значением: '{item_value}'")
        
        if not item_value:
            logger.warning("Не указано значение для фильтрации, возвращаем все данные")
            return df.copy(), {}
        
        # Проверяем наличие колонки
        if column_name not in df.columns:
            logger.warning(f"Колонка '{column_name}' не найдена в данных")
            return df.copy(), {}
        
        # df нечувствительная к регистру:
        filtered_df = df[df[column_name].str.lower() == item_value.lower()].copy()
        
        # Если не найдено элементов, возвращаем пустой DataFrame
        if len(filtered_df) == 0:
            logger.warning(f"Не найдено элементов со значением '{item_value}' в колонке '{column_name}'")
            return pd.DataFrame(), {}
        
        # Создаем словарь с оценками релевантности (все строки с равной оценкой)
        scores = {idx: 1.0 for idx in filtered_df.index}
        
        logger.info(f"Найдено {len(filtered_df)} элементов")
        return filtered_df, scores
    
    def _build_classification_prompts(self, question: str) -> Dict[str, str]:
        """
        Строит промпты для классификации запроса.
        
        :param question: Вопрос пользователя
        :return: Словарь с системным и пользовательским промптами
        """
        from app.utils.prompt_builder import PromptBuilder
        
        # Используем универсальный метод PromptBuilder
        return PromptBuilder.build_classification_prompt(
            question=question,
            items=self.items_list,
            item_type=self.get_item_type()
        )