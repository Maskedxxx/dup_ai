# app/tools/base_tool.py

import pandas as pd
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
from app.utils.logging import setup_logger

# Настройка логгера
logger = setup_logger(__name__)


class BaseTool(ABC):
    """
    Абстрактный базовый класс для всех инструментов.
    Определяет контракт: каждый инструмент должен иметь схему и метод выполнения.
    """
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """
        Возвращает JSON-схему инструмента для OpenAI function calling.
        
        :return: Словарь со схемой.
        """
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> Tuple[pd.DataFrame, Dict[int, float]]:
        """
        Выполняет логику инструмента.
        
        :param kwargs: Аргументы, извлеченные LLM из запроса пользователя.
                       Также должен включать 'df' (DataFrame для обработки).
        :return: Кортеж (Отфильтрованный DataFrame, Словарь с оценками релевантности)
        """
        pass


def calculate_relevance_score(text: str, keywords: List[str]) -> float:
    """
    Вычисляет оценку релевантности текста на основе ключевых слов.
    Базовая реализация - количество найденных ключевых слов.
    
    :param text: Текст для анализа
    :param keywords: Список ключевых слов
    :return: Оценка релевантности (0.0 - 1.0)
    """
    if not text or not keywords:
        return 0.0
    
    text_lower = str(text).lower()
    matches = 0
    
    for keyword in keywords:
        keyword_lower = keyword.lower().strip()
        if keyword_lower and keyword_lower in text_lower:
            matches += 1
    
    # Нормализуем по количеству ключевых слов
    return matches / len(keywords) if keywords else 0.0