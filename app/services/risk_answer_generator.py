# app/services/risk_answer_generator.py

from typing import List, Dict, Any
from app.services.base_answer_generator import BaseAnswerGeneratorService
from app.domain.models.risk import Risk
from app.domain.models.answer import Answer
from app.utils.logging import setup_logger
from app.utils.prompt_builder import PromptBuilder

# Настройка логгера
logger = setup_logger(__name__)


class RiskAnswerGeneratorService(BaseAnswerGeneratorService):
    """
    Сервис для генерации ответов на основе данных о рисках.
    """
    
    def _convert_item_to_dict(self, item: Risk) -> Dict[str, Any]:
        """
        Преобразует риск в словарь для промпта.
        
        :param item: Модель риска
        :return: Словарь с данными риска
        """
        return {
            "project_name": item.project_name,
            "risk_text": item.risk_text,
            "risk_priority": item.risk_priority,
            "status": item.status,
            "measures": item.measures,  # <--- ДОБАВЛЕНО
            "project_id": item.project_id,
            "project_type": item.project_type,
            "relevance_score": item.relevance_score
        }
    
    def _get_prompts(self, question: str, items_data: List[Dict[str, Any]], **kwargs) -> Dict[str, str]:
        """
        Получает промпты для генерации ответа о рисках.
        
        :param question: Вопрос пользователя
        :param items_data: Список данных рисков
        :param kwargs: Дополнительные параметры (category, additional_context)
        :return: Словарь с промптами
        """
        category = kwargs.get('category', '')
        additional_context = kwargs.get('additional_context', '')
        return PromptBuilder.build_risk_answer_prompt(question, items_data, category, additional_context)
    
    def _generate_fallback_text(self, question: str, items: List[Risk], **kwargs) -> str:
        """
        Генерирует fallback текст для рисков.
        
        :param question: Вопрос пользователя
        :param items: Список рисков
        :param kwargs: Дополнительные параметры (category)
        :return: Fallback текст
        """
        category = kwargs.get('category', '')
        fallback_text = f"По вашему запросу '{question}' в категории '{category}' найдено {len(items)} рисков."
        
        if items:
            fallback_text += "\n\n## Список рисков:\n\n"
            for i, risk in enumerate(items, 1):
                fallback_text += f"{i}. **Проект**: {risk.project_name}\n   **Риск**: {risk.risk_text}\n\n"
        
        return fallback_text
    
    def make_md(self, question: str, risks: List[Risk], category: str, additional_context: str = "") -> Answer:
        """
        Совместимость с существующим кодом - принимает category как отдельный параметр.
        
        :param question: Вопрос пользователя
        :param risks: Список рисков
        :param category: Категория риска
        :param additional_context: Дополнительный контекст
        :return: Модель Answer
        """
        return super().make_md(question, risks, additional_context=additional_context, category=category)