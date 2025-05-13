# app/services/risk_normalization.py

import pandas as pd
import json
from typing import Dict
from app.services.base_normalization import BaseNormalizationService
from app.utils.logging import setup_logger

# Настройка логгера
logger = setup_logger(__name__)


class RiskNormalizationService(BaseNormalizationService):
    """
    Сервис для нормализации данных о рисках.
    """
    
    def get_column_mapping(self) -> Dict[str, str]:
        """
        Возвращает маппинг колонок для данных о рисках.
        
        :return: Словарь соответствия старых и новых названий колонок
        """
        return {
            '№ проекта': 'project_id',
            'Тип проекта': 'project_type',
            'Наименование проекта': 'project_name',
            'Риск': 'risk_json',
            'Приоритетность': 'risk_priority',
            'Текущий статус': 'status',
            'Вероятность': 'probability',
            'Серьезность последствий': 'severity',
            'Предлагаемые меры': 'proposed_measures'
        }
    
    def _additional_processing(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Дополнительная обработка для извлечения текста риска из JSON.
        
        :param df: DataFrame после базовой нормализации
        :return: DataFrame с добавленной колонкой risk_text
        """
        # Экстрагируем текст риска из JSON
        if 'risk_json' in df.columns:
            df['risk_text'] = df['risk_json'].apply(self._extract_risk_text)
        
        return df
    
    def _extract_risk_text(self, risk_json: str) -> str:
        """
        Извлекает текст риска из JSON строки.
        
        :param risk_json: JSON строка с данными о риске
        :return: Текст риска
        """
        try:
            risk_data = json.loads(risk_json)
            # Возвращаем значение ключа "original" или пустую строку
            return risk_data.get("original", "")
        except (json.JSONDecodeError, TypeError):
            # В случае ошибки возвращаем исходный текст
            return str(risk_json)