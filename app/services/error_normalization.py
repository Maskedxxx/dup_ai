# app/services/error_normalization.py

from typing import Dict
from app.services.base_normalization import BaseNormalizationService
from app.utils.logging import setup_logger

# Настройка логгера
logger = setup_logger(__name__)


class ErrorNormalizationService(BaseNormalizationService):
    """
    Сервис для нормализации данных об ошибках.
    """
    
    def get_column_mapping(self) -> Dict[str, str]:
        """
        Возвращает маппинг колонок для данных об ошибках.
        
        :return: Словарь соответствия старых и новых названий колонок
        """
        return {
            'дата фиксации': 'date',
            'ответственный': 'responsible',
            'предмет ошибки': 'subject',
            'описание ошибки': 'description',
            'предпринятые меры': 'measures',
            'причина': 'reason',
            'проект': 'project',
            'стадия проекта': 'stage',
            'категория': 'category'
        }