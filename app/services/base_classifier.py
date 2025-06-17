# app/services/base_classifier.py

import pandas as pd
from typing import Dict, List, Tuple, Type, get_origin, get_args
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field, create_model
from app.adapters.llm_client import LLMClient
from app.utils.logging import setup_logger

# Настройка логгера
logger = setup_logger(__name__)


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
    
    def _create_dynamic_classification_model(self, items: List[str]) -> Type[BaseModel]:
        """
        Создает динамическую модель Pydantic с Literal для точного выбора элементов.
        
        :param items: Список доступных элементов для выбора
        :return: Класс модели Pydantic
        """
        if not items:
            logger.warning("Пустой список элементов для создания модели")
            items = ["Нет данных"]
        
        # Создаем Literal тип из списка элементов
        from typing import Literal
        literal_type = Literal[tuple(items)]
        
        # Создаем модель для одного результата сопоставления
        MatchResultWithLiteral = create_model(
            'MatchResultWithLiteral',
            item=(literal_type, Field(..., description="Выбранный элемент из списка")),
            score=(float, Field(..., ge=0, le=1, description="Оценка релевантности от 0 до 1"))
        )
        
        # Создаем основную модель результата классификации
        ClassificationResult = create_model(
            'ClassificationResult',
            reasoning=(str, Field(..., description="Краткое рассуждение о классификации")),
            top_matches=(List[MatchResultWithLiteral], Field(..., 
                description="Топ-3 элемента с оценками релевантности", 
                min_items=1, max_items=3))
        )
        
        logger.debug(f"Создана динамическая модель для {len(items)} элементов")
        return ClassificationResult
    
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
        
        # Создаем динамическую модель для текущего списка элементов
        classification_model = self._create_dynamic_classification_model(self.items_list)
        
        # Получаем промпты для классификации
        prompts = self._build_classification_prompts(question)
        
        try:
            # Вызываем API для структурированного ответа
            result = self.llm_client.generate_structured_completion(
                system_prompt=prompts['system'],
                user_prompt=prompts['user'],
                response_model=classification_model,
                temperature=0
            )
            
            if result and hasattr(result, 'top_matches'):
                top_matches = result.top_matches
                logger.info(f"Рассуждение модели: {result.reasoning}")
                
                # Логируем все результаты
                for i, match in enumerate(top_matches, 1):
                    logger.info(f"Вариант {i}: {match.item} (оценка: {match.score})")
                
                # Возвращаем элемент с наивысшей оценкой
                if top_matches:
                    best_match = max(top_matches, key=lambda x: x.score)
                    logger.info(f"Выбран элемент: {best_match.item} с оценкой {best_match.score}")
                    return best_match.item
            
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
        
        # Фильтрация с учетом регистра
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