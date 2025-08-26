# app/services/contractor_normalization.py

from typing import Dict
from app.services.base_normalization import BaseNormalizationService
from app.utils.logging import setup_logger

# Настройка логгера
logger = setup_logger(__name__)


class ContractorNormalizationService(BaseNormalizationService):
    """
    Сервис для нормализации данных о подрядчиках.
    """
    
    def get_column_mapping(self) -> Dict[str, str]:
        """
        Возвращает маппинг колонок для данных о подрядчиках.
        
        :return: Словарь соответствия старых и новых названий колонок
        """
        return {
            'Наименование_КА': 'name',
            'Виды_работ': 'work_types',
            'Контактное_лицо': 'contact_person',
            'Контакты': 'contacts',
            'Сайт': 'website',
            'Задействован_в_проекте': 'projects',
            'Комментарий': 'comments',
            'Первичная_информация': 'primary_info',
            'Штат': 'staff_size'
        }
