import pandas as pd
from typing import Dict, List, Tuple
from pydantic import BaseModel, Field
from app.adapters.llm_client import LLMClient
from app.utils.logging import setup_logger
from app.utils.prompt_builder import PromptBuilder

# Настройка логгера
logger = setup_logger("error_classifier")

class ProjectClassificationResult(BaseModel):
    """Результат классификации запроса по проектам."""
    reasoning: str = Field(..., description="Краткое рассуждение о том, к какому проекту относится вопрос")
    top_projects: Dict[str, float] = Field(..., description="Топ-3 проекта с оценками релевантности (от 0 до 1)")

class ErrorClassifierService:
    """
    Сервис для классификации запросов об ошибках и определения релевантных проектов.
    """
    
    def __init__(self, llm_client: LLMClient):
        """
        Инициализация сервиса классификации.
        
        :param llm_client: Клиент для взаимодействия с LLM
        """
        self.llm_client = llm_client
        self.project_names: List[str] = []
        logger.info("Инициализирован сервис классификации ошибок")
    
    def load_project_names(self, df: pd.DataFrame) -> List[str]:
        """
        Загружает список уникальных названий проектов из DataFrame.
        
        :param df: DataFrame с данными об ошибках
        :return: Список уникальных названий проектов
        """
        try:
            # Получаем уникальные значения из колонки 'project'
            if 'project' in df.columns:
                # Фильтруем пустые значения и преобразуем в список
                unique_names = df['project'].dropna().unique().tolist()
                
                # Фильтруем пустые строки
                unique_names = [name for name in unique_names if name and isinstance(name, str)]
                
                logger.info(f"Загружено {len(unique_names)} уникальных названий проектов: {unique_names}")
                self.project_names = unique_names
                return unique_names
            else:
                logger.warning("Колонка 'project' не найдена в данных")
                return []
        except Exception as e:
            logger.error(f"Ошибка при загрузке названий проектов: {e}")
            return []
    
    def classify(self, question: str) -> str:
        """
        Классифицирует вопрос пользователя и определяет наиболее релевантный проект.
        
        :param question: Вопрос пользователя
        :return: Наиболее релевантное название проекта
        """
        logger.info(f"Классификация запроса об ошибках: '{question}'")
        
        if not self.project_names:
            logger.warning("Список названий проектов пуст, невозможно классифицировать запрос")
            return ""
        
        # Получаем промпты для классификации по проектам
        prompts = PromptBuilder.build_error_project_classification_prompt(question, self.project_names)
        
        try:
            # Вызываем API для структурированного ответа
            result = self.llm_client.generate_structured_completion(
                system_prompt=prompts['system'],
                user_prompt=prompts['user'],
                response_model=ProjectClassificationResult,
                temperature=0
            )
            
            if result and hasattr(result, 'top_projects'):
                top_projects = result.top_projects
                logger.info(f"Топ-3 проекта: {top_projects}")
                
                # Находим проект с наивысшей оценкой
                if top_projects:
                    best_project = max(top_projects.items(), key=lambda x: x[1])
                    logger.info(f"Выбран проект: {best_project[0]} с оценкой {best_project[1]}")
                    
                    # Возвращаем название наиболее релевантного проекта
                    return best_project[0]
            
            logger.warning("Модель не вернула структурированный ответ с проектами")
            return ""
                
        except Exception as e:
            logger.error(f"Ошибка при классификации запроса об ошибках: {e}")
            return ""
    
    def filter_errors(self, df: pd.DataFrame, project_name: str) -> Tuple[pd.DataFrame, Dict[int, float]]:
        """
        Фильтрует DataFrame по названию проекта.
        
        :param df: DataFrame с данными об ошибках
        :param project_name: Название проекта для фильтрации
        :return: Кортеж из отфильтрованного DataFrame и словаря оценок
        """
        logger.info(f"Фильтрация ошибок по названию проекта: '{project_name}'")
        
        if not project_name:
            logger.warning("Не указано название проекта для фильтрации, возвращаем все данные")
            return df.copy(), {}
        
        # Проверяем наличие колонки 'project'
        if 'project' not in df.columns:
            logger.warning("Колонка 'project' не найдена в данных")
            return df.copy(), {}
        
        filtered_df = df[df['project'] == project_name].copy()
        
        # Если не найдено ошибок для данного проекта, возвращаем пустой DataFrame
        if len(filtered_df) == 0:
            logger.warning(f"Не найдено ошибок для проекта '{project_name}'")
            return pd.DataFrame(), {}
        
        # Создаем словарь с оценками релевантности (все строки с равной оценкой)
        scores = {idx: 1.0 for idx in filtered_df.index}
        
        logger.info(f"Найдено {len(filtered_df)} ошибок для проекта '{project_name}'")
        return filtered_df, scores