# app/services/contractor_answer_generator.py

from typing import List, Dict, Any
from app.services.base_answer_generator import BaseAnswerGeneratorService
from app.domain.models.contractor import Contractor
from app.utils.logging import setup_logger
from app.utils.prompt_builder import PromptBuilder

# Настройка логгера
logger = setup_logger(__name__)


class AnswerGeneratorService(BaseAnswerGeneratorService):
    """
    Сервис для генерации ответов на основе данных о подрядчиках.
    """
    
    def _convert_item_to_dict(self, item: Contractor) -> Dict[str, Any]:
        """
        Преобразует подрядчика в словарь для промпта.
        
        :param item: Модель подрядчика
        :return: Словарь с данными подрядчика
        """
        return {
            "content": f"Название: {item.name}\nВиды работ: {item.work_types}\nКонтактное лицо: {item.contact_person}\nКонтакты: {item.contacts}",
            "metadata": {
                "website": item.website,
                "projects": item.projects,
                "comments": item.comments,
                "primary_info": item.primary_info,
                "staff_size": item.staff_size,
                "relevance_score": item.relevance_score
            }
        }
    
    def _get_prompts(self, question: str, items_data: List[Dict[str, Any]], **kwargs) -> Dict[str, str]:
        """
        Получает промпты для генерации ответа о подрядчиках.
        
        :param question: Вопрос пользователя
        :param items_data: Список данных подрядчиков
        :param kwargs: Дополнительные параметры (additional_context)
        :return: Словарь с промптами
        """
        additional_context = kwargs.get('additional_context', '')
        return PromptBuilder.build_answer_prompt(question, items_data, additional_context)
    
    def _generate_fallback_text(self, question: str, items: List[Contractor], **kwargs) -> str:
        """
        Генерирует fallback текст для подрядчиков.
        
        :param question: Вопрос пользователя
        :param items: Список подрядчиков
        :return: Fallback текст
        """
        fallback_text = f"По вашему запросу '{question}' найдено {len(items)} подрядчиков."
        
        if items:
            fallback_text += "\n\n## Список подрядчиков:\n\n"
            for i, c in enumerate(items, 1):
                fallback_text += f"{i}. **{c.name}** - {c.work_types}\n"
        
        return fallback_text