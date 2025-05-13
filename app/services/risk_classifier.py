# app/services/risk_classifier.py

from app.services.base_classifier import BaseClassifierService
from app.utils.logging import setup_logger

# Настройка логгера
logger = setup_logger(__name__)


class RiskClassifierService(BaseClassifierService):
    """
    Сервис для классификации запросов о рисках.
    """
    
    def get_column_name(self) -> str:
        """
        Возвращает название колонки для извлечения проектов.
        
        :return: Название колонки 'project_name'
        """
        return 'project_name'
    
    def get_item_type(self) -> str:
        """
        Возвращает тип элементов для промптов.
        
        :return: Тип элементов 'проект'
        """
        return 'проект'
    
    # Специфичные методы для рисков
    def load_project_names(self, df):
        """Совместимость с существующим кодом."""
        return self.load_items(df)
    
    def filter_risks(self, df, project_name):
        """Совместимость с существующим кодом."""
        return self.filter_items(df, project_name)