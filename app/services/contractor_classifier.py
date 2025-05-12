# app/services/contractor_classifier.py

import pandas as pd
from typing import Dict, List, Tuple
from pydantic import BaseModel, Field
from app.adapters.llm_client import LLMClient
from app.utils.logging import setup_logger
from app.utils.prompt_builder import PromptBuilder

# Настройка логгера
logger = setup_logger(__name__)

class ClassificationResult(BaseModel):
    """Результат классификации запроса."""
    reasoning: str = Field(..., description="Краткое рассуждение о том, к какому проекту относится вопрос")
    top_projects: Dict[str, float] = Field(..., description="Топ-3 проекта с оценками релевантности (от 0 до 1)")

class ContractorClassifierService:
    """
    Сервис для классификации запросов и определения релевантных типов работ.
    """
    
    def __init__(self, llm_client: LLMClient):
        """
        Инициализация сервиса классификации.
        
        :param llm_client: Клиент для взаимодействия с LLM
        """
        self.llm_client = llm_client
        self.work_types: List[str] = []
        logger.info("Инициализирован сервис классификации подрядчиков")
    
    def load_work_types(self, df: pd.DataFrame) -> List[str]:
        """
        Загружает список уникальных типов работ из DataFrame.
        
        :param df: DataFrame с данными о подрядчиках
        :return: Список уникальных типов работ
        """
        try:
            # Получаем уникальные значения из колонки 'work_types'
            if 'work_types' in df.columns:
                # Фильтруем пустые значения и преобразуем в список
                unique_work_types = df['work_types'].dropna().unique().tolist()
                
                # Фильтруем пустые строки
                unique_work_types = [work for work in unique_work_types if work and isinstance(work, str)]
                
                logger.info(f"Загружено {len(unique_work_types)} уникальных видов работ")
                self.work_types = unique_work_types
                return unique_work_types
            else:
                logger.warning("Колонка 'work_types' не найдена в данных")
                return []
        except Exception as e:
            logger.error(f"Ошибка при загрузке видов работ: {e}")
            return []
    
    def classify(self, question: str) -> str:
        """
        Классифицирует вопрос пользователя и определяет наиболее релевантный тип работ.
        
        :param question: Вопрос пользователя
        :return: Наиболее релевантный тип работ
        """
        logger.info(f"Классификация запроса: '{question}'")
        
        if not self.work_types:
            logger.warning("Список типов работ пуст, невозможно классифицировать запрос")
            return ""
        
        # Получаем промпты для классификации
        prompts = PromptBuilder.build_classification_prompt(question, self.work_types)
        
        try:
            # Вызываем API для структурированного ответа
            result = self.llm_client.generate_structured_completion(
                system_prompt=prompts['system'],
                user_prompt=prompts['user'],
                response_model=ClassificationResult,
                temperature=0
            )
            
            if result and hasattr(result, 'top_projects'):
                top_projects = result.top_projects
                logger.info(f"Рассуждение модели: {result.reasoning}")
                logger.info(f"Топ-3 проекта: {top_projects}")
                
                # Находим проект с наивысшей оценкой
                if top_projects:
                    best_project = max(top_projects.items(), key=lambda x: x[1])
                    logger.info(f"Выбран проект: {best_project[0]} с оценкой {best_project[1]}")
                    
                    # Возвращаем имя наиболее релевантного проекта
                    return best_project[0]
            
            logger.warning("Модель не вернула структурированный ответ с проектами")
            return ""
                
        except Exception as e:
            logger.error(f"Ошибка при классификации запроса: {e}")
            return ""
    
    def filter_contractors(self, df: pd.DataFrame, work_type: str) -> Tuple[pd.DataFrame, Dict[int, float]]:
        """
        Фильтрует DataFrame по определенному типу работ.
        
        :param df: DataFrame с данными подрядчиков
        :param work_type: Тип работ для фильтрации
        :return: Кортеж из отфильтрованного DataFrame и словаря оценок
        """
        logger.info(f"Фильтрация подрядчиков по типу работ: '{work_type}'")
        
        if not work_type:
            logger.warning("Не указан тип работ для фильтрации, возвращаем все данные")
            return df.copy(), {}
        
        # Проверяем наличие колонки 'work_types'
        if 'work_types' not in df.columns:
            logger.warning("Колонка 'work_types' не найдена в данных")
            return df.copy(), {}
        
        filtered_df = df[df['work_types'] == work_type].copy()
        
        # Если не найдено подрядчиков для данного типа работ, возвращаем пустой DataFrame
        if len(filtered_df) == 0:
            logger.warning(f"Не найдено подрядчиков для типа работ '{work_type}'")
            return pd.DataFrame(), {}
        
        # Создаем словарь с оценками релевантности (все строки с равной оценкой)
        scores = {idx: 1.0 for idx in filtered_df.index}
        
        logger.info(f"Найдено {len(filtered_df)} подрядчиков для типа работ '{work_type}'")
        return filtered_df, scores