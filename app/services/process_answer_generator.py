# app/services/process_answer_generator.py

from typing import List, Dict, Any
from app.services.base_answer_generator import BaseAnswerGeneratorService
from app.domain.models.process import Process
from app.utils.logging import setup_logger
from app.utils.prompt_builder import PromptBuilder

# Настройка логгера
logger = setup_logger(__name__)


class ProcessAnswerGeneratorService(BaseAnswerGeneratorService):
    """
    Сервис для генерации ответов на основе данных о бизнес-процессах.
    """
    
    def _convert_item_to_dict(self, item: Process) -> Dict[str, Any]:
        """
        Преобразует процесс в словарь для промпта.
        
        :param item: Модель процесса
        :return: Словарь с данными процесса
        """
        return {
            "id": item.id,
            "name": item.name,
            "description": item.description,
            "json_file": item.json_file,
            "text_description": item.text_description,
            "relevance_score": item.relevance_score
        }
    
    def _get_prompts(self, question: str, items_data: List[Dict[str, Any]], **kwargs) -> Dict[str, str]:
        """
        Получает промпты для генерации ответа о процессах.
        
        :param question: Вопрос пользователя
        :param items_data: Список данных процессов
        :param kwargs: Дополнительные параметры (additional_context)
        :return: Словарь с промптами
        """
        additional_context = kwargs.get('additional_context', '')
        return PromptBuilder.build_process_answer_prompt(question, items_data, additional_context)
    
    def _generate_fallback_text(self, question: str, items: List[Process], **kwargs) -> str:
        """
        Генерирует fallback текст для процессов.
        
        :param question: Вопрос пользователя
        :param items: Список процессов
        :return: Fallback текст
        """
        fallback_text = f"По вашему запросу '{question}' найдено {len(items)} бизнес-процессов."
        
        if items:
            fallback_text += "\n\n## Список бизнес-процессов:\n\n"
            for i, process in enumerate(items, 1):
                fallback_text += f"{i}. **{process.name}**\n   {process.description}\n\n"
        
        return fallback_text