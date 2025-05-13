# app/services/contractor_classifier.py

from app.services.base_classifier import BaseClassifierService
from app.utils.logging import setup_logger

# Настройка логгера
logger = setup_logger(__name__)


class ContractorClassifierService(BaseClassifierService):
    """
    Сервис для классификации запросов о подрядчиках.
    """
    
    def get_column_name(self) -> str:
        """
        Возвращает название колонки для извлечения видов работ.
        
        :return: Название колонки 'work_types'
        """
        return 'work_types'
    
    def get_item_type(self) -> str:
        """
        Возвращает тип элементов для промптов.
        
        :return: Тип элементов 'проект'
        """
        return 'проект'
    
    # Специфичные методы для контракторов
    def load_work_types(self, df):
        """Совместимость с существующим кодом."""
        return self.load_items(df)
    
    def filter_contractors(self, df, work_type):
        """Совместимость с существующим кодом."""
        return self.filter_items(df, work_type)