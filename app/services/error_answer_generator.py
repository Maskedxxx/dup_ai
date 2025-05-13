# app/services/error_answer_generator.py

from typing import List, Dict, Any
from app.services.base_answer_generator import BaseAnswerGeneratorService
from app.domain.models.error import Error
from app.utils.logging import setup_logger
from app.utils.prompt_builder import PromptBuilder

# Настройка логгера
logger = setup_logger(__name__)


class ErrorAnswerGeneratorService(BaseAnswerGeneratorService):
    """
    Сервис для генерации ответов на основе данных об ошибках.
    """
    
    def _convert_item_to_dict(self, item: Error) -> Dict[str, Any]:
        """
        Преобразует ошибку в словарь для промпта.
        
        :param item: Модель ошибки
        :return: Словарь с данными ошибки
        """
        return {
            "date": item.date,
            "responsible": item.responsible,
            "subject": item.subject,
            "description": item.description,
            "measures": item.measures,
            "reason": item.reason,
            "project": item.project,
            "stage": item.stage,
            "category": item.category,
            "relevance_score": item.relevance_score
        }
    
    def _get_prompts(self, question: str, items_data: List[Dict[str, Any]], **kwargs) -> Dict[str, str]:
        """
        Получает промпты для генерации ответа об ошибках.
        
        :param question: Вопрос пользователя
        :param items_data: Список данных ошибок
        :param kwargs: Дополнительные параметры (additional_context)
        :return: Словарь с промптами
        """
        additional_context = kwargs.get('additional_context', '')
        return PromptBuilder.build_error_answer_prompt(question, items_data, additional_context)
    
    def _generate_fallback_text(self, question: str, items: List[Error], **kwargs) -> str:
        """
        Генерирует fallback текст для ошибок.
        
        :param question: Вопрос пользователя
        :param items: Список ошибок
        :return: Fallback текст
        """
        fallback_text = f"По вашему запросу '{question}' найдено {len(items)} ошибок."
        
        if items:
            fallback_text += "\n\n## Список ошибок:\n\n"
            for i, error in enumerate(items, 1):
                fallback_text += f"{i}. **Проект**: {error.project}\n   **Описание**: {error.description}\n\n"
        
        return fallback_text