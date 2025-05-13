# app/services/process_classifier.py

from app.services.base_classifier import BaseClassifierService
from app.utils.logging import setup_logger

# Настройка логгера
logger = setup_logger(__name__)


class ProcessClassifierService(BaseClassifierService):
    """
    Сервис для классификации запросов о бизнес-процессах.
    """
    
    def get_column_name(self) -> str:
        """
        Возвращает название колонки для извлечения процессов.
        
        :return: Название колонки 'name'
        """
        return 'name'
    
    def get_item_type(self) -> str:
        """
        Возвращает тип элементов для промптов.
        
        :return: Тип элементов 'бизнес-процесс'
        """
        return 'бизнес-процесс'
    
    # Специфичные методы для процессов
    def load_process_names(self, df):
        """Совместимость с существующим кодом."""
        return self.load_items(df)
    
    def filter_processes(self, df, process_name):
        """Совместимость с существующим кодом."""
        return self.filter_items(df, process_name)