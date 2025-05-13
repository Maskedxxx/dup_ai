# app/services/base_answer_generator.py

from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from pydantic import BaseModel
from app.adapters.llm_client import LLMClient
from app.domain.models.answer import Answer
from app.utils.logging import setup_logger

# Настройка логгера
logger = setup_logger(__name__)


class BaseAnswerGeneratorService(ABC):
    """
    Базовый класс для всех сервисов генерации ответов.
    Предоставляет общую логику для создания ответов на основе данных.
    """
    
    def __init__(self, llm_client: LLMClient):
        """
        Инициализация сервиса.
        
        :param llm_client: Клиент для взаимодействия с LLM
        """
        self.llm_client = llm_client
        logger.info(f"Инициализирован {self.__class__.__name__}")
    
    @abstractmethod
    def _convert_item_to_dict(self, item: BaseModel) -> Dict[str, Any]:
        """
        Преобразует элемент модели в словарь для промпта.
        Должен быть реализован в наследниках.
        
        :param item: Элемент данных (Contractor, Risk, Error, Process)
        :return: Словарь с данными для промпта
        """
        pass
    
    @abstractmethod
    def _get_prompts(self, question: str, items_data: List[Dict[str, Any]], **kwargs) -> Dict[str, str]:
        """
        Получает промпты для генерации ответа.
        Должен быть реализован в наследниках.
        
        :param question: Вопрос пользователя
        :param items_data: Список данных элементов
        :param kwargs: Дополнительные параметры (например, категория для рисков)
        :return: Словарь с системным и пользовательским промптами
        """
        pass
    
    @abstractmethod
    def _generate_fallback_text(self, question: str, items: List[BaseModel], **kwargs) -> str:
        """
        Генерирует fallback текст в случае ошибки.
        Должен быть реализован в наследниках.
        
        :param question: Вопрос пользователя
        :param items: Список элементов
        :param kwargs: Дополнительные параметры
        :return: Fallback текст
        """
        pass
    
    def make_md(self, question: str, items: List[BaseModel], additional_context: str = "", **kwargs) -> Answer:
        """
        Генерирует markdown-ответ на основе вопроса и данных.
        
        :param question: Вопрос пользователя
        :param items: Список элементов (Contractor, Risk, Error, Process)
        :param additional_context: Дополнительный контекст для генерации ответа
        :param kwargs: Дополнительные параметры специфичные для типа данных
        :return: Модель Answer с сгенерированным ответом
        """
        logger.info(f"Генерация ответа на вопрос: '{question}'")
        
        # Преобразуем элементы в формат для промпта
        items_data = [self._convert_item_to_dict(item) for item in items]
        
        # Объединяем дополнительный контекст с kwargs для удобства
        if additional_context:
            kwargs['additional_context'] = additional_context
        
        # Получаем промпты для генерации ответа
        prompts = self._get_prompts(question, items_data, **kwargs)
        
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
                total_found=len(items),
                items=items,
                meta=kwargs.get('meta'),
                category=kwargs.get('category')
            )
            
            return answer
            
        except Exception as e:
            logger.error(f"Ошибка при генерации ответа: {e}")
            
            # В случае ошибки возвращаем базовый ответ
            fallback_text = self._generate_fallback_text(question, items, **kwargs)
            
            return Answer(
                text=fallback_text,
                query=question,
                total_found=len(items),
                items=items,
                meta=kwargs.get('meta'),
                category=kwargs.get('category')
            )