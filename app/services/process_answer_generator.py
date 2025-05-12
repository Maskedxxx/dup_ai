# app/services/process_answer_generator.py

from typing import List, Dict, Any
from app.adapters.llm_client import LLMClient
from app.domain.models.process import Process
from app.domain.models.answer import Answer
from app.utils.logging import setup_logger
from app.utils.prompt_builder import PromptBuilder

# Настройка логгера
logger = setup_logger("process_answer_generator")

class ProcessAnswerGeneratorService:
    """
    Сервис для генерации ответов на основе данных о бизнес-процессах.
    """
    
    def __init__(self, llm_client: LLMClient):
        """
        Инициализация сервиса.
        
        :param llm_client: Клиент для взаимодействия с LLM
        """
        self.llm_client = llm_client
        logger.info("Инициализирован сервис генерации ответов о бизнес-процессах")
    
    def make_md(self, question: str, processes: List[Process], additional_context: str = "") -> Answer:
        """
        Генерирует markdown-ответ на основе вопроса и данных о бизнес-процессах.
        
        :param question: Вопрос пользователя
        :param processes: Список процессов
        :param additional_context: Дополнительный контекст для генерации ответа
        :return: Модель Answer с сгенерированным ответом
        """
        logger.info(f"Генерация ответа на вопрос о бизнес-процессах: '{question}'")
        
        # Преобразуем процессы в формат для промпта
        processes_data = [
            {
                "id": process.id,
                "name": process.name,
                "description": process.description,
                "json_file": process.json_file,
                "text_description": process.text_description,
                "relevance_score": process.relevance_score
            }
            for process in processes
        ]
        
        # Получаем промпты для генерации ответа
        prompts = PromptBuilder.build_process_answer_prompt(question, processes_data, additional_context)
        
        try:
            # Генерируем ответ с помощью LLM
            generated_text = self.llm_client.generate_completion(
                system_prompt=prompts['system'],
                user_prompt=prompts['user'],
                temperature=0.2
            )
            
            logger.info(f"Сгенерирован ответ о бизнес-процессах длиной {len(generated_text) if generated_text else 0} символов")
            
            # Формируем модель ответа
            answer = Answer(
                text=generated_text,
                query=question,
                total_found=len(processes),
                items=processes
            )
            
            return answer
            
        except Exception as e:
            logger.error(f"Ошибка при генерации ответа о бизнес-процессах: {e}")
            
            # В случае ошибки возвращаем базовый ответ
            fallback_text = f"По вашему запросу '{question}' найдено {len(processes)} бизнес-процессов."
            
            if processes:
                fallback_text += "\n\n## Список бизнес-процессов:\n\n"
                for i, process in enumerate(processes, 1):
                    fallback_text += f"{i}. **{process.name}**\n   {process.description}\n\n"
            
            return Answer(
                text=fallback_text,
                query=question,
                total_found=len(processes),
                items=processes
            )