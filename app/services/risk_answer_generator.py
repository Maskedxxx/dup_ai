from typing import List, Dict, Any
from app.adapters.llm_client import LLMClient
from app.domain.models.risk import Risk
from app.domain.models.answer import Answer
from app.utils.logging import setup_logger
from app.utils.prompt_builder import PromptBuilder

# Настройка логгера
logger = setup_logger(__name__)

class RiskAnswerGeneratorService:
    """
    Сервис для генерации ответов на основе данных о рисках.
    """
    
    def __init__(self, llm_client: LLMClient):
        """
        Инициализация сервиса.
        
        :param llm_client: Клиент для взаимодействия с LLM
        """
        self.llm_client = llm_client
        logger.info("Инициализирован сервис генерации ответов о рисках")
    
    def make_md(self, question: str, risks: List[Risk], category: str, additional_context: str = "") -> Answer:
        """
        Генерирует markdown-ответ на основе вопроса и данных о рисках.
        
        :param question: Вопрос пользователя
        :param risks: Список рисков
        :param category: Категория риска
        :param additional_context: Дополнительный контекст для генерации ответа
        :return: Модель Answer с сгенерированным ответом
        """
        logger.info(f"Генерация ответа на вопрос о рисках: '{question}', категория: {category}")
        
        # Преобразуем риски в формат для промпта
        risks_data = [
            {
                "project_name": risk.project_name,
                "risk_text": risk.risk_text,
                "risk_priority": risk.risk_priority,
                "status": risk.status,
                "project_id": risk.project_id,
                "project_type": risk.project_type,
                "relevance_score": risk.relevance_score
            }
            for risk in risks
        ]
        
        # Получаем промпты для генерации ответа
        prompts = PromptBuilder.build_risk_answer_prompt(question, risks_data, category, additional_context)
        
        try:
            # Генерируем ответ с помощью LLM
            generated_text = self.llm_client.generate_completion(
                system_prompt=prompts['system'],
                user_prompt=prompts['user'],
                temperature=0.7  # Немного креативности для более человечного ответа
            )
            
            logger.info(f"Сгенерирован ответ о рисках длиной {len(generated_text) if generated_text else 0} символов")
            
            # Формируем модель ответа
            answer = Answer(
                text=generated_text,
                query=question,
                total_found=len(risks),
                items=risks,
                category=category
            )
            
            return answer
            
        except Exception as e:
            logger.error(f"Ошибка при генерации ответа о рисках: {e}")
            
            # В случае ошибки возвращаем базовый ответ
            fallback_text = f"По вашему запросу '{question}' в категории '{category}' найдено {len(risks)} рисков."
            
            if risks:
                fallback_text += "\n\n## Список рисков:\n\n"
                for i, risk in enumerate(risks, 1):
                    fallback_text += f"{i}. **Проект**: {risk.project_name}\n   **Риск**: {risk.risk_text}\n\n"
            
            return Answer(
                text=fallback_text,
                query=question,
                total_found=len(risks),
                items=risks,
                category=category
            )