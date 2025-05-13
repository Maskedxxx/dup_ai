# app/services/process_normalization.py

from typing import Dict
from app.services.base_normalization import BaseNormalizationService
from app.utils.logging import setup_logger

# Настройка логгера
logger = setup_logger(__name__)


class ProcessNormalizationService(BaseNormalizationService):
    """
    Сервис для нормализации данных о бизнес-процессах.
    """
    
    def get_column_mapping(self) -> Dict[str, str]:
        """
        Возвращает маппинг колонок для данных о бизнес-процессах.
        
        :return: Словарь соответствия старых и новых названий колонок
        """
        return {
            'ID': 'id',
            'Название процесса': 'name',
            'Описание': 'description',
            'Файл JSON': 'json_file',
            'Текстовое описание': 'text_description'
        }