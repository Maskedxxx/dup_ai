# app/services/base_normalization.py

import pandas as pd
from abc import ABC, abstractmethod
from typing import Dict
from app.utils.logging import setup_logger

# Настройка логгера
logger = setup_logger(__name__)


class BaseNormalizationService(ABC):
    """
    Базовый класс для всех сервисов нормализации данных.
    Предоставляет общую логику очистки и нормализации DataFrame.
    """
    
    @abstractmethod
    def get_column_mapping(self) -> Dict[str, str]:
        """
        Возвращает словарь маппинга колонок.
        Должен быть реализован в наследниках.
        
        :return: Словарь {старое_название: новое_название}
        """
        pass
    
    def clean_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Очищает и нормализует DataFrame с данными.
        
        :param df: Исходный DataFrame
        :return: Нормализованный DataFrame
        """
        logger.info(f"Начало нормализации данных. Исходное количество строк: {len(df)}")
        
        # Получаем маппинг колонок из наследника
        column_mapping = self.get_column_mapping()
        
        # Переименовываем колонки, если они есть
        df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns}, inplace=True)
        
        # Логируем информацию о колонках
        logger.info(f"Колонки после переименования: {', '.join(df.columns)}")
        
        # Заполняем пустые значения и нормализуем текстовые поля
        for col in df.columns:
            if df[col].dtype == 'object':  # Строковые колонки
                # Заполняем пустые значения пустой строкой
                df[col] = df[col].fillna('')
                # Удаляем лишние пробелы в начале и конце
                df[col] = df[col].astype(str).str.strip()
                # Нормализуем пробелы между словами (убираем двойные пробелы)
                df[col] = df[col].str.replace(r'\s+', ' ', regex=True)
        
        # Вызываем дополнительную обработку, если она нужна
        df = self._additional_processing(df)
        
        logger.info(f"Данные успешно нормализованы. Конечное количество строк: {len(df)}")
        return df
    
    def _additional_processing(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Метод для дополнительной обработки данных.
        Может быть переопределен в наследниках для специфичной логики.
        
        :param df: DataFrame после базовой нормализации
        :return: DataFrame после дополнительной обработки
        """
        return df