# app/tools/keyword_search_tool.py

import pandas as pd
from typing import List, Dict, Any, Tuple
from app.tools.base_tool import BaseTool, calculate_relevance_score
from app.utils.logging import setup_logger

# Настройка логгера
logger = setup_logger(__name__)


class KeywordSearchTool(BaseTool):
    """
    Инструмент для фильтрации DataFrame по ключевым словам в указанной колонке.
    """
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Возвращает схему для поиска по ключевым словам.
        Схема теперь более общая и включает параметр 'column_to_search'.
        """
        return {
            "type": "function",
            "function": {
                "name": "search_by_keywords",
                "description": "Ищет записи по ключевым словам в указанной текстовой колонке.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "keywords": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Список ключевых слов для поиска."
                        },
                        "column_to_search": {
                            "type": "string",
                            "description": "Название колонки в DataFrame, по которой будет производиться поиск."
                        }
                    },
                    "required": ["keywords", "column_to_search"],
                    "additionalProperties": False
                },
                "strict": True
            }
        }

    def execute(self, df: pd.DataFrame, keywords: List[str], column_to_search: str, top_n: int = 3, **kwargs) -> Tuple[pd.DataFrame, Dict[int, float]]:
        """
        Выполняет фильтрацию DataFrame по ключевым словам.
        
        :param df: DataFrame для фильтрации.
        :param keywords: Список ключевых слов.
        :param column_to_search: Колонка для поиска.
        :param top_n: Количество топ записей для возврата.
        :return: Кортеж (Отфильтрованный DataFrame, Словарь с оценками релевантности).
        """
        if df.empty or not keywords:
            logger.warning("Пустой DataFrame или список ключевых слов для KeywordSearchTool.")
            return df.head(top_n), {}
        
        if column_to_search not in df.columns:
            logger.warning(f"Колонка '{column_to_search}' не найдена в DataFrame.")
            return df.head(top_n), {}
        
        logger.info(f"KeywordSearchTool: Поиск по ключевым словам '{keywords}' в колонке '{column_to_search}'.")
        
        df_with_scores = df.copy()
        df_with_scores['keyword_relevance_score'] = df_with_scores[column_to_search].apply(
            lambda text: calculate_relevance_score(text, keywords)
        )
        
        filtered_df = df_with_scores[df_with_scores['keyword_relevance_score'] > 0]
        
        if filtered_df.empty:
            logger.warning("KeywordSearchTool: Не найдено совпадений. Возвращаем топ-N из исходных данных.")
            # Возвращаем исходный df, но с пустыми скорами
            return df.head(top_n), {}
        
        result_df = filtered_df.nlargest(top_n, 'keyword_relevance_score')
        
        # Создаем словарь с оценками релевантности
        scores = pd.Series(result_df.keyword_relevance_score, index=result_df.index).to_dict()
        
        logger.info(f"KeywordSearchTool: Найдено {len(filtered_df)} совпадений, возвращаем топ {len(result_df)}.")
        
        return result_df, scores