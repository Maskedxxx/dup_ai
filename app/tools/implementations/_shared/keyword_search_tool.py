# app/tools/keyword_search_tool.py

import pandas as pd
import pymorphy3
import re
from typing import List, Dict, Any, Tuple
from app.tools.base_tool import BaseTool, calculate_relevance_score
from app.utils.logging import setup_logger

# Настройка логгера
logger = setup_logger(__name__)

# Инициализация pymorphy2.MorphAnalyzer один раз для производительности
morph = pymorphy3.MorphAnalyzer()

class KeywordSearchTool(BaseTool):
    """
    Инструмент для фильтрации DataFrame по ключевым словам в колонке 'risk_text'
    с использованием лемматизации для более точного поиска.
    """

    def _lemmatize_text(self, text: str) -> str:
        """
        Приводит текст к нижнему регистру, удаляет знаки препинания и лемматизирует слова.
        """
        if not isinstance(text, str):
            return ""
        text = text.lower()
        # Удаляем все, кроме букв, цифр и пробелов
        text = re.sub(r'[^а-яА-Яa-zA-Z0-9\s]', ' ', text)
        words = text.split()
        lemmatized_words = [morph.parse(word)[0].normal_form for word in words]
        return " ".join(lemmatized_words)

    def get_schema(self) -> Dict[str, Any]:
        """
        Возвращает схему для поиска по ключевым словам.
        """
        return {
            "type": "function",
            "function": {
                "name": "search_by_keywords",
                "description": "Ищет риски по ключевым словам в их описании (поле risk_text).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "keywords": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Список ключевых слов для поиска в описании риска."
                        }
                    },
                    "required": ["keywords"],
                    "additionalProperties": False
                },
                "strict": True
            }
        }

    def execute(self, df: pd.DataFrame, keywords: List[str], top_n: int = 3, **kwargs) -> Tuple[pd.DataFrame, Dict[int, float]]:
        """
        Выполняет фильтрацию DataFrame по ключевым словам в колонке 'risk_text' с лемматизацией.

        :param df: DataFrame для фильтрации.
        :param keywords: Список ключевых слов.
        :param top_n: Количество топ записей для возврата.
        :return: Кортеж (Отфильтрованный DataFrame, Словарь с оценками релевантности).
        """
        if df.empty or not keywords:
            logger.warning("Пустой DataFrame или список ключевых слов для KeywordSearchTool.")
            return df.head(top_n), {}

        column_to_search = "risk_text"

        if column_to_search not in df.columns:
            logger.error(f"Критическая ошибка: колонка '{column_to_search}' не найдена в DataFrame.")
            return pd.DataFrame(), {}

        logger.info(f"KeywordSearchTool: Оригинальные ключевые слова: {keywords}")
        
        # Лемматизация ключевых слов
        lemmatized_keywords = [self._lemmatize_text(kw) for kw in keywords if kw]
        logger.info(f"KeywordSearchTool: Лемматизированные ключевые слова: {lemmatized_keywords}")

        # Лемматизация колонки для поиска
        lemmatized_column_name = f"lemmatized_{column_to_search}"
        df_with_scores = df.copy()
        df_with_scores[lemmatized_column_name] = df_with_scores[column_to_search].apply(self._lemmatize_text)

        logger.info(f"Поиск по лемматизированным ключевым словам в лемматизированной колонке '{lemmatized_column_name}'.")

        # Расчет релевантности на основе лемматизированных данных
        logger.info("Начинаем расчет релевантности для найденных записей...")
        df_with_scores['keyword_relevance_score'] = df_with_scores[lemmatized_column_name].apply(
            lambda text: calculate_relevance_score(text, lemmatized_keywords, enable_detailed_logging=True)
        )

        filtered_df = df_with_scores[df_with_scores['keyword_relevance_score'] > 0]

        if filtered_df.empty:
            logger.warning("KeywordSearchTool: Не найдено совпадений после лемматизации.")
            return df.head(top_n), {}

        result_df = filtered_df.nlargest(top_n, 'keyword_relevance_score')

        # Создаем словарь с оценками релевантности
        scores = pd.Series(result_df.keyword_relevance_score, index=result_df.index).to_dict()

        logger.info(f"KeywordSearchTool: Найдено {len(filtered_df)} совпадений, возвращаем топ {len(result_df)}.")

        # Возвращаем оригинальные данные, без временных колонок
        return df.loc[result_df.index], scores