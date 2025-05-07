import pandas as pd
import json
from app.utils.logging import setup_logger

# Настройка логгера
logger = setup_logger(__name__)

class RiskNormalizationService:
    """
    Сервис для нормализации и очистки данных о рисках.
    """
    
    @staticmethod
    def clean_df(df: pd.DataFrame) -> pd.DataFrame:
        """
        Очищает и нормализует DataFrame с данными о рисках.
        
        :param df: Исходный DataFrame
        :return: Нормализованный DataFrame
        """
        logger.info(f"Начало нормализации данных о рисках. Исходное количество строк: {len(df)}")
        
        # Проверяем и переименовываем колонки при необходимости
        column_mapping = {
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
        
        # Переименовываем колонки, если они есть
        df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns}, inplace=True)
        
        # Логируем информацию о колонках
        logger.info(f"Колонки после переименования: {', '.join(df.columns)}")
        
        # Экстрагируем текст риска из JSON
        if 'risk_json' in df.columns:
            df['risk_text'] = df['risk_json'].apply(RiskNormalizationService.extract_risk_text)
        
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
    
    @staticmethod
    def extract_risk_text(risk_json: str) -> str:
        """
        Извлекает текст риска из JSON строки.
        
        :param risk_json: JSON строка с данными о риске
        :return: Текст риска
        """
        try:
            risk_data = json.loads(risk_json)
            # Возвращаем значение ключа "original" (приоритет) или пустую строку если ключа нет
            return risk_data.get("original", "")
        except (json.JSONDecodeError, TypeError):
            # В случае ошибки возвращаем исходный текст
            return str(risk_json)