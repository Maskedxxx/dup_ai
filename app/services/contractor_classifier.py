# app/services/contractor_classifier.py

from app.services.base_classifier import BaseClassifierService
from app.utils.logging import setup_logger
from app.adapters.llm_client import LLMClient

# Настройка логгера
logger = setup_logger(__name__)


class ContractorClassifierService(BaseClassifierService):
    """
    Сервис для классификации запросов о подрядчиках.
    Использует единую конфигурацию классификации.
    """
    
    def __init__(self, llm_client: LLMClient):
        """
        Инициализация сервиса классификации подрядчиков.
        
        :param llm_client: Клиент для взаимодействия с LLM
        """
        super().__init__(llm_client, entity_type="CONTRACTOR")
    
    def _get_column_name_fallback(self) -> str:
        """
        Fallback метод для получения имени колонки.
        Используется если конфигурация не загружена.
        """
        return 'work_types'
    
    def _get_item_type_fallback(self) -> str:
        """
        Fallback метод для получения типа элементов.
        Используется если конфигурация не загружена.
        """
        return 'вид работ'
    
    # Специфичные методы для контракторов
    def load_work_types(self, df):
        """Совместимость с существующим кодом."""
        return self.load_items(df)
    
    def filter_contractors(self, df, work_type):
        """Совместимость с существующим кодом."""
        return self.filter_items(df, work_type)