# app/services/base_classifier.py

import pandas as pd
from typing import Dict, List, Tuple, Type
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field, create_model
from app.adapters.llm_client import LLMClient
from app.utils.logging import setup_logger, get_pipeline_logger

# Настройка логгера
logger = setup_logger(__name__)


class BaseClassifierService(ABC):
    """
    Базовый класс для всех сервисов классификации.
    Предоставляет общую логику для классификации запросов.
    """
    
    def __init__(self, llm_client: LLMClient, entity_type: str = None):
        """
        Инициализация сервиса классификации.
        
        :param llm_client: Клиент для взаимодействия с LLM
        :param entity_type: Тип сущности для получения конфигурации из ClassificationConfig
        """
        self.llm_client = llm_client
        self.items_list: List[str] = []
        self.pipeline_logger = get_pipeline_logger(f"{self.__class__.__name__}")
        
        # Загружаем конфигурацию если указан тип сущности
        self._classification_config = {}
        if entity_type:
            from app.config import classification_config
            self._classification_config = classification_config.get_config(entity_type)
            logger.info(f"Загружена конфигурация для типа '{entity_type}': {self._classification_config}")
        
        logger.info(f"Инициализирован {self.__class__.__name__}")
    
    def get_column_name(self) -> str:
        """
        Возвращает название колонки для извлечения элементов.
        Использует конфигурацию если доступна, иначе абстрактный метод.
        
        :return: Название колонки в DataFrame
        """
        if self._classification_config and 'column_name' in self._classification_config:
            return self._classification_config['column_name']
        return self._get_column_name_fallback()
    
    def get_item_type(self) -> str:
        """
        Возвращает тип элементов для использования в промптах.
        Использует конфигурацию если доступна, иначе абстрактный метод.
        
        :return: Тип элементов (например, "проект", "процесс")
        """
        if self._classification_config and 'item_type' in self._classification_config:
            return self._classification_config['item_type']
        return self._get_item_type_fallback()
    
    def _get_column_name_fallback(self) -> str:
        """
        Fallback метод для получения имени колонки.
        Должен быть переопределен в наследниках, если не используется конфиг.
        """
        raise NotImplementedError("Необходимо переопределить _get_column_name_fallback или передать entity_type в конструктор")
    
    def _get_item_type_fallback(self) -> str:
        """
        Fallback метод для получения типа элементов.
        Должен быть переопределен в наследниках, если не используется конфиг.
        """
        raise NotImplementedError("Необходимо переопределить _get_item_type_fallback или передать entity_type в конструктор")
    
    def _preprocess_items_with_hashtags(self, items: List[str]) -> List[str]:
        """
        Предобрабатывает элементы, добавляя хештег-разделители для улучшения классификации LLM.
        Использует символ # как разделитель сущностей - максимально обученный LLM паттерн.
        
        :param items: Исходный список элементов
        :return: Обработанный список с хештег-разделителями
        """
        if not items:
            return items
            
        processed_items = []
        for item in items:
            # Добавляем хештег в начало и конец для четкого разделения сущности
            processed_item = f"#{item}#"
            processed_items.append(processed_item)
            
        logger.debug(f"Предобработано {len(processed_items)} элементов с хештег-разделителями")
        return processed_items

    def _remove_hashtag_separators(self, item_with_hashtags: str) -> str:
        """
        Удаляет хештег-разделители из элемента, возвращая исходное значение.
        
        :param item_with_hashtags: Элемент с хештег-разделителями (#item#)
        :return: Очищенный элемент
        """
        if not item_with_hashtags:
            return item_with_hashtags
            
        # Убираем хештеги в начале и конце
        cleaned = item_with_hashtags.strip('#')
        return cleaned

    def _create_dynamic_classification_model(self, items: List[str]) -> Type[BaseModel]:
        """
        Создает динамическую модель Pydantic с Literal для точного выбора элементов.
        Применяет предобработку с хештег-разделителями для улучшения классификации.
        
        :param items: Список доступных элементов для выбора
        :return: Класс модели Pydantic
        """
        if not items:
            logger.warning("Пустой список элементов для создания модели")
            items = ["Нет данных"]
        
        # Применяем предобработку с хештег-разделителями
        processed_items = self._preprocess_items_with_hashtags(items)
        
        # Создаем Literal тип из списка обработанных элементов
        from typing import Literal
        literal_type = Literal[tuple(processed_items)]
        
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
        self.pipeline_logger.log_detail(f"Начинаем классификацию запроса: '{question}'")
        
        if not self.items_list:
            self.pipeline_logger.log_detail("Список элементов пуст, невозможно классифицировать запрос", "WARNING")
            return ""
        
        self.pipeline_logger.log_detail(f"Доступно элементов для классификации: {len(self.items_list)}")
        
        # Создаем динамическую модель для текущего списка элементов
        self.pipeline_logger.log_detail("Создаем динамическую модель классификации")
        classification_model = self._create_dynamic_classification_model(self.items_list)
        
        # Получаем промпты для классификации
        self.pipeline_logger.log_detail("Формируем промпты для классификации")
        prompts = self._build_classification_prompts(question)
        
        # Логируем полные промпты в детальном режиме
        self.pipeline_logger.log_prompt_details(
            prompt_type="classification",
            system_prompt=prompts['system'],
            user_prompt=prompts['user']
        )
        
        try:
            # Вызываем API для структурированного ответа
            self.pipeline_logger.log_detail("Отправляем запрос к LLM для классификации")
            result = self.llm_client.generate_structured_completion(
                system_prompt=prompts['system'],
                user_prompt=prompts['user'],
                response_model=classification_model,
                temperature=0
            )
            
            if result and hasattr(result, 'top_matches'):
                top_matches = result.top_matches
                
                # Логируем результат классификации
                self.pipeline_logger.log_detail(f"Рассуждение модели: {result.reasoning}")
                
                # Логируем все результаты
                for i, match in enumerate(top_matches, 1):
                    self.pipeline_logger.log_detail(f"Вариант {i}: {match.item} (оценка: {match.score})")
                
                # Логируем полный ответ LLM в детальном режиме
                self.pipeline_logger.log_prompt_details(
                    prompt_type="classification",
                    system_prompt="",  # Пустые, так как уже залогированы выше
                    user_prompt="",
                    response=str(result)
                )
                
                # Возвращаем элемент с наивысшей оценкой
                if top_matches:
                    best_match = max(top_matches, key=lambda x: x.score)
                    
                    # Убираем хештег-разделители из результата
                    clean_item = self._remove_hashtag_separators(best_match.item)
                    
                    self.pipeline_logger.log_detail(f"Выбран лучший элемент: '{clean_item}' с оценкой {best_match.score}")
                    return clean_item
            
            self.pipeline_logger.log_detail("Модель не вернула структурированный ответ", "WARNING")
            return ""
                
        except Exception as e:
            self.pipeline_logger.log_detail(f"Ошибка при классификации запроса: {e}", "ERROR")
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