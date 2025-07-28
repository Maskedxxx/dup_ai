# app/tools/base_tool.py

import pandas as pd
from abc import ABC, abstractmethod
from typing import List
from app.utils.logging import setup_logger

# Настройка логгера
logger = setup_logger(__name__)


class BaseTool(ABC):
    """
    Абстрактный базовый класс для всех инструментов фильтрации.
    """
    
    @abstractmethod
    def filter(self, df: pd.DataFrame, keywords: List[str], top_n: int = 3) -> pd.DataFrame:
        """
        Фильтрует DataFrame на основе ключевых слов.
        
        :param df: DataFrame для фильтрации
        :param keywords: Список ключевых слов для поиска
        :param top_n: Количество топ записей для возврата
        :return: Отфильтрованный DataFrame с топ записями
        """
        pass
    
    def _calculate_relevance_score(self, text: str, keywords: List[str]) -> float:
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