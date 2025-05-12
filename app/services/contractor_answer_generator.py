# app/services/contractor_answer_generator.py

from typing import List, Dict, Any
from app.adapters.llm_client import LLMClient
from app.domain.models.contractor import Contractor
from app.domain.models.answer import Answer
from app.utils.logging import setup_logger
from app.utils.prompt_builder import PromptBuilder

# Настройка логгера
logger = setup_logger(__name__)

class AnswerGeneratorService:
    """
    Сервис для генерации ответов на основе данных о подрядчиках.
    """
    
    def __init__(self, llm_client: LLMClient):
        """
        Инициализация сервиса.
        
        :param llm_client: Клиент для взаимодействия с LLM
        """
        self.llm_client = llm_client
        logger.info("Инициализирован сервис генерации ответов")
    
    def make_md(self, question: str, contractors: List[Contractor], additional_context: str = "") -> Answer:
        """
        Генерирует markdown-ответ на основе вопроса и данных о подрядчиках.
        
        :param question: Вопрос пользователя
        :param contractors: Список подрядчиков
        :param additional_context: Дополнительный контекст для генерации ответа
        :return: Модель Answer с сгенерированным ответом
        """
        logger.info(f"Генерация ответа на вопрос: '{question}'")
        
        # Преобразуем contractors в документы для генератора
        documents = [
            {
                "content": f"Название: {c.name}\nВиды работ: {c.work_types}\nКонтактное лицо: {c.contact_person}\nКонтакты: {c.contacts}",
                "metadata": {
                    "website": c.website,
                    "projects": c.projects,
                    "comments": c.comments,
                    "primary_info": c.primary_info,
                    "staff_size": c.staff_size,
                    "relevance_score": c.relevance_score
                }
            }
            for c in contractors
        ]
        
        # Получаем промпты для генерации ответа
        prompts = PromptBuilder.build_answer_prompt(question, documents, additional_context)
        
        try:
            # Генерируем ответ с помощью LLM
            generated_text = self.llm_client.generate_completion(
                system_prompt=prompts['system'],
                user_prompt=prompts['user'],
                temperature=0.2  # Немного креативности для более человечного ответа
            )
            
            logger.info(f"Сгенерирован ответ длиной {len(generated_text) if generated_text else 0} символов")
            
            # Формируем модель ответа
            answer = Answer(
                text=generated_text,
                query=question,
                total_found=len(contractors),
                items=contractors
            )
            
            return answer
            
        except Exception as e:
            logger.error(f"Ошибка при генерации ответа: {e}")
            
            # В случае ошибки возвращаем базовый ответ
            fallback_text = f"По вашему запросу '{question}' найдено {len(contractors)} подрядчиков."
            
            if contractors:
                fallback_text += "\n\n## Список подрядчиков:\n\n"
                for i, c in enumerate(contractors, 1):
                    fallback_text += f"{i}. **{c.name}** - {c.work_types}\n"
            
            return Answer(
                text=fallback_text,
                query=question,
                total_found=len(contractors),
                items=contractors
            )