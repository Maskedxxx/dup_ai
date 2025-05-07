from typing import List, Dict, Any
from app.adapters.llm_client import LLMClient
from app.domain.models.error import Error
from app.domain.models.answer import Answer
from app.utils.logging import setup_logger
from app.utils.prompt_builder import PromptBuilder

# Настройка логгера
logger = setup_logger("error_answer_generator")

class ErrorAnswerGeneratorService:
    """
    Сервис для генерации ответов на основе данных об ошибках.
    """
    
    def __init__(self, llm_client: LLMClient):
        """
        Инициализация сервиса.
        
        :param llm_client: Клиент для взаимодействия с LLM
        """
        self.llm_client = llm_client
        logger.info("Инициализирован сервис генерации ответов об ошибках")
    
    def make_md(self, question: str, errors: List[Error], additional_context: str = "") -> Answer:
        """
        Генерирует markdown-ответ на основе вопроса и данных об ошибках.
        
        :param question: Вопрос пользователя
        :param errors: Список ошибок
        :param additional_context: Дополнительный контекст для генерации ответа
        :return: Модель Answer с сгенерированным ответом
        """
        logger.info(f"Генерация ответа на вопрос об ошибках: '{question}'")
        
        # Преобразуем ошибки в формат для промпта
        errors_data = [
            {
                "date": error.date,
                "responsible": error.responsible,
                "subject": error.subject,
                "description": error.description,
                "measures": error.measures,
                "reason": error.reason,
                "project": error.project,
                "stage": error.stage,
                "category": error.category,
                "relevance_score": error.relevance_score
            }
            for error in errors
        ]
        
        # Получаем промпты для генерации ответа
        prompts = PromptBuilder.build_error_answer_prompt(question, errors_data, additional_context)
        
        try:
            # Генерируем ответ с помощью LLM
            generated_text = self.llm_client.generate_completion(
                system_prompt=prompts['system'],
                user_prompt=prompts['user'],
                temperature=0.2  # Немного креативности для более человечного ответа
            )
            
            logger.info(f"Сгенерирован ответ об ошибках длиной {len(generated_text) if generated_text else 0} символов")
            
            # Формируем модель ответа
            answer = Answer(
                text=generated_text,
                query=question,
                total_found=len(errors),
                items=errors
            )
            
            return answer
            
        except Exception as e:
            logger.error(f"Ошибка при генерации ответа об ошибках: {e}")
            
            # В случае ошибки возвращаем базовый ответ
            fallback_text = f"По вашему запросу '{question}' найдено {len(errors)} ошибок."
            
            if errors:
                fallback_text += "\n\n## Список ошибок:\n\n"
                for i, error in enumerate(errors, 1):
                    fallback_text += f"{i}. **Проект**: {error.project}\n   **Описание**: {error.description}\n\n"
            
            return Answer(
                text=fallback_text,
                query=question,
                total_found=len(errors),
                items=errors
            )