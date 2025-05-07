import pandas as pd
from fastapi import HTTPException
from app.config import contractor_settings, risk_settings, error_settings
from app.utils.logging import setup_logger
from app.domain.enums import ButtonType

# Настройка логгера
logger = setup_logger(__name__)

class ExcelLoader:
    """
    Адаптер для загрузки данных из Excel файла.
    """
    
    @staticmethod
    def load(button_type: ButtonType = None) -> pd.DataFrame:
        """
        Загружает данные из Excel-файла в зависимости от типа кнопки.
        
        :param button_type: Тип кнопки (contractors или risks)
        :return: DataFrame с данными из файла
        :raises HTTPException 500: если не удалось загрузить файл
        """
        # Определяем путь к файлу в зависимости от типа кнопки
        if button_type == ButtonType.RISKS:
            file_path = risk_settings.data_file_path
        elif button_type == ButtonType.ERRORS:
            file_path = error_settings.data_file_path
        else:
            # По умолчанию загружаем файл подрядчиков
            file_path = contractor_settings.data_file_path
            
        logger.info(f"Загрузка данных из файла: {file_path}")
        try:
            df = pd.read_excel(file_path)
            logger.info(f"Данные успешно загружены. Количество строк: {len(df)}")
            return df
        except Exception as e:
            error_msg = f"Ошибка чтения файла данных: {e}"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)