# app/tools/keyword_search_tool.py

import pandas as pd
from typing import List
from app.utils.logging import setup_logger

# Настройка логгера
logger = setup_logger(__name__)


def filter_risks_by_keywords(df: pd.DataFrame, keywords: List[str], top_n: int = 3) -> pd.DataFrame:
    """
    Простая функция для фильтрации рисков по ключевым словам.
    
    :param df: DataFrame с рисками
    :param keywords: Список ключевых слов для поиска  
    :param top_n: Количество топ записей для возврата
    :return: Отфильтрованный DataFrame
    """
    if df.empty or not keywords:
        logger.warning("Пустой DataFrame или список ключевых слов")
        return df.head(top_n)
    
    if 'risk_text' not in df.columns:
        logger.warning("Колонка 'risk_text' не найдена в DataFrame")
        return df.head(top_n)
    
    logger.info(f"Поиск по ключевым словам: {keywords}")
    
    # Вычисляем релевантность для каждой строки
    df_with_scores = df.copy()
    df_with_scores['keyword_relevance_score'] = df_with_scores['risk_text'].apply(
        lambda text: _calculate_relevance_score(text, keywords)
    )
    
    # Фильтруем строки с релевантностью > 0
    filtered_df = df_with_scores[df_with_scores['keyword_relevance_score'] > 0]
    
    # Fallback: если ничего не найдено, возвращаем все
    if filtered_df.empty:
        logger.warning("Не найдено совпадений по ключевым словам. Возвращаем все записи.")
        return df.head(top_n)
    
    # Сортируем по релевантности и берем топ N
    result_df = filtered_df.nlargest(top_n, 'keyword_relevance_score')
    
    logger.info(f"Найдено {len(filtered_df)} совпадений, возвращаем топ {min(top_n, len(result_df))}")
    
    return result_df


def _calculate_relevance_score(text: str, keywords: List[str]) -> float:
    """
    Вычисляет оценку релевантности текста на основе ключевых слов.
    Использует частичные совпадения.
    
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