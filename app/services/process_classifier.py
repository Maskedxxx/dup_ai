# app/services/process_classifier.py

from app.services.base_classifier import BaseClassifierService
from app.utils.logging import setup_logger
from app.adapters.llm_client import LLMClient

# Настройка логгера
logger = setup_logger(__name__)


class ProcessClassifierService(BaseClassifierService):
    """
    Сервис для классификации запросов о бизнес-процессах.
    Использует единую конфигурацию классификации.
    """
    
    def __init__(self, llm_client: LLMClient):
        """
        Инициализация сервиса классификации процессов.
        
        :param llm_client: Клиент для взаимодействия с LLM
        """
        super().__init__(llm_client, entity_type="PROCESS")
    
    def _get_column_name_fallback(self) -> str:
        """
        Fallback метод для получения имени колонки.
        Используется если конфигурация не загружена.
        """
        return 'process_name'
    
    def _get_item_type_fallback(self) -> str:
        """
        Fallback метод для получения типа элементов.
        Используется если конфигурация не загружена.
        """
        return 'процесс'
    
    # Специфичные методы для процессов
    def load_process_names(self, df):
        """Совместимость с существующим кодом."""
        return self.load_items(df)
    
    def filter_processes(self, df, process_name):
        """Совместимость с существующим кодом."""
        return self.filter_items(df, process_name)