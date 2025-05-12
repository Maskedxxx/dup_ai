# app/services/process_normalization.py

import pandas as pd
from app.utils.logging import setup_logger

# Настройка логгера
logger = setup_logger("process_normalization")

class ProcessNormalizationService:
    """
    Сервис для нормализации и очистки данных о бизнес-процессах.
    """
    
    @staticmethod
    def clean_df(df: pd.DataFrame) -> pd.DataFrame:
        """
        Очищает и нормализует DataFrame с данными о бизнес-процессах.
        
        :param df: Исходный DataFrame
        :return: Нормализованный DataFrame
        """
        logger.info(f"Начало нормализации данных о бизнес-процессах. Исходное количество строк: {len(df)}")
        
        # Проверяем и переименовываем колонки при необходимости
        column_mapping = {
            'ID': 'id',
            'Название процесса': 'name',
            'Описание': 'description',
            'Файл JSON': 'json_file',
            'Текстовое описание': 'text_description'
        }
        
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
        
        logger.info(f"Данные успешно нормализованы. Конечное количество строк: {len(df)}")
        return df