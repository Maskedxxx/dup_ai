# app/pipelines/base.py

from abc import ABC, abstractmethod
from app.domain.models.answer import Answer
from app.utils.logging import setup_logger

# Настройка логгера
logger = setup_logger(__name__)

class Pipeline(ABC):
    """
    Абстрактный базовый класс для всех пайплайнов.
    """
    
    @abstractmethod
    def process(self, question: str) -> Answer:
        """
        Обрабатывает вопрос и возвращает ответ.
        
        :param question: Вопрос пользователя
        :return: Модель Answer с результатом обработки
        """
        pass