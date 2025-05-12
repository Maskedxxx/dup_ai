# app/services/process_classifier.py

import pandas as pd
from typing import Dict, List, Tuple
from pydantic import BaseModel, Field
from app.adapters.llm_client import LLMClient
from app.utils.logging import setup_logger
from app.utils.prompt_builder import PromptBuilder

# Настройка логгера
logger = setup_logger("process_classifier")

class ProcessClassificationResult(BaseModel):
    """Результат классификации запроса по процессам."""
    reasoning: str = Field(..., description="Краткое рассуждение о том, к какому процессу относится вопрос")
    top_processes: Dict[str, float] = Field(..., description="Топ-3 процесса с оценками релевантности (от 0 до 1)")

class ProcessClassifierService:
    """
    Сервис для классификации запросов о бизнес-процессах.
    """
    
    def __init__(self, llm_client: LLMClient):
        """
        Инициализация сервиса классификации.
        
        :param llm_client: Клиент для взаимодействия с LLM
        """
        self.llm_client = llm_client
        self.process_names: List[str] = []
        logger.info("Инициализирован сервис классификации бизнес-процессов")
    
    def load_process_names(self, df: pd.DataFrame) -> List[str]:
        """
        Загружает список уникальных названий процессов из DataFrame.
        
        :param df: DataFrame с данными о бизнес-процессах
        :return: Список уникальных названий процессов
        """
        try:
            # Получаем уникальные значения из колонки 'name'
            if 'name' in df.columns:
                # Фильтруем пустые значения и преобразуем в список
                unique_names = df['name'].dropna().unique().tolist()
                
                # Фильтруем пустые строки
                unique_names = [name for name in unique_names if name and isinstance(name, str)]
                
                logger.info(f"Загружено {len(unique_names)} уникальных названий процессов: {unique_names}")
                self.process_names = unique_names
                return unique_names
            else:
                logger.warning("Колонка 'name' не найдена в данных")
                return []
        except Exception as e:
            logger.error(f"Ошибка при загрузке названий процессов: {e}")
            return []
    
    def classify(self, question: str) -> str:
        """
        Классифицирует вопрос пользователя и определяет наиболее релевантный процесс.
        
        :param question: Вопрос пользователя
        :return: Наиболее релевантное название процесса
        """
        logger.info(f"Классификация запроса о бизнес-процессах: '{question}'")
        
        if not self.process_names:
            logger.warning("Список названий процессов пуст, невозможно классифицировать запрос")
            return ""
        
        # Получаем промпты для классификации по процессам
        prompts = PromptBuilder.build_process_classification_prompt(question, self.process_names)
        
        try:
            # Вызываем API для структурированного ответа
            result = self.llm_client.generate_structured_completion(
                system_prompt=prompts['system'],
                user_prompt=prompts['user'],
                response_model=ProcessClassificationResult,
                temperature=0
            )
            
            if result and hasattr(result, 'top_processes'):
                top_processes = result.top_processes
                logger.info(f"Рассуждение модели: {result.reasoning}")
                logger.info(f"Топ-3 процесса: {top_processes}")
                
                # Находим процесс с наивысшей оценкой
                if top_processes:
                    best_process = max(top_processes.items(), key=lambda x: x[1])
                    logger.info(f"Выбран процесс: {best_process[0]} с оценкой {best_process[1]}")
                    
                    # Возвращаем название наиболее релевантного процесса
                    return best_process[0]
            
            logger.warning("Модель не вернула структурированный ответ с процессами")
            return ""
                
        except Exception as e:
            logger.error(f"Ошибка при классификации запроса о бизнес-процессах: {e}")
            return ""
    
    def filter_processes(self, df: pd.DataFrame, process_name: str) -> Tuple[pd.DataFrame, Dict[int, float]]:
        """
        Фильтрует DataFrame по названию процесса.
        
        :param df: DataFrame с данными о бизнес-процессах
        :param process_name: Название процесса для фильтрации
        :return: Кортеж из отфильтрованного DataFrame и словаря оценок
        """
        logger.info(f"Фильтрация процессов по названию: '{process_name}'")
        
        if not process_name:
            logger.warning("Не указано название процесса для фильтрации, возвращаем все данные")
            return df.copy(), {}
        
        # Проверяем наличие колонки 'name'
        if 'name' not in df.columns:
            logger.warning("Колонка 'name' не найдена в данных")
            return df.copy(), {}
        
        filtered_df = df[df['name'] == process_name].copy()
        
        # Если не найдено процессов для данного названия, возвращаем пустой DataFrame
        if len(filtered_df) == 0:
            logger.warning(f"Не найдено процессов с названием '{process_name}'")
            return pd.DataFrame(), {}
        
        # Создаем словарь с оценками релевантности (все строки с равной оценкой)
        scores = {idx: 1.0 for idx in filtered_df.index}
        
        logger.info(f"Найдено {len(filtered_df)} процессов с названием '{process_name}'")
        return filtered_df, scores