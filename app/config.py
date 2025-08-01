# app/config.py

from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Dict, Type, Optional, Any, List
from enum import Enum

class BaseAppSettings(BaseSettings):
    model_config = ConfigDict(
        env_file='.env',
        extra='allow',
        env_prefix=''
    )

class AppSettings(BaseAppSettings):
    """Основные настройки приложения."""
    app_name: str
    environment: str
    debug: bool
    host: str
    port: int
    reload: bool

class ContractorSettings(BaseAppSettings):
    """Настройки для подрядчиков."""
    model_config = ConfigDict(
        env_file='.env',
        extra='allow',
        env_prefix='CONTRACTOR_'
    )
    
    data_file_path: str
    max_results: int = 20

class RiskSettings(BaseAppSettings):
    """Настройки для рисков."""
    model_config = ConfigDict(
        env_file='.env',
        extra='allow',
        env_prefix='RISK_'
    )
    
    data_file_path: str
    max_results: int = 20

class ErrorSettings(BaseAppSettings):
    """Настройки для ошибок."""
    model_config = ConfigDict(
        env_file='.env',
        extra='allow',
        env_prefix='ERROR_'
    )
    
    data_file_path: str
    max_results: int = 20

class ProcessSettings(BaseAppSettings):
    """Настройки для процессов."""
    model_config = ConfigDict(
        env_file='.env',
        extra='allow',
        env_prefix='PROCESS_'
    )
    
    data_file_path: str
    max_results: int = 20

class LLMSettings(BaseAppSettings):
    """Настройки для LLM клиента."""
    model_config = ConfigDict(
        env_file='.env',
        extra='allow',
        env_prefix='LLM_'  # Используем общий префикс из .env
    )
    
    # Настройки LLM
    ollama_base_url: str
    ollama_api_key: str
    ollama_model: str

# Создание экземпляров настроек
app_settings = AppSettings()
llm_settings = LLMSettings()
contractor_settings = ContractorSettings()
risk_settings = RiskSettings()
error_settings = ErrorSettings()
process_settings = ProcessSettings()

# DI контейнер
class Container:
    """Простой контейнер для управления зависимостями."""
    def __init__(self):
        self._instances: Dict[Type, Any] = {}
        self._factories: Dict[Type, callable] = {}
    
    def register(self, cls: Type, instance: Any) -> None:
        """Регистрирует экземпляр класса в контейнере."""
        self._instances[cls] = instance
    
    def register_factory(self, cls: Type, factory: callable) -> None:
        """Регистрирует фабрику для создания экземпляров."""
        self._factories[cls] = factory
    
    def get(self, cls: Type) -> Optional[Any]:
        """Возвращает экземпляр класса из контейнера."""
        # Сначала проверяем существующие экземпляры
        if cls in self._instances:
            return self._instances[cls]
        
        # Если есть фабрика, используем её
        if cls in self._factories:
            instance = self._factories[cls]()
            self._instances[cls] = instance
            return instance
        
        return None
    
    def clear(self) -> None:
        """Очищает контейнер."""
        self._instances.clear()
        self._factories.clear()

container = Container()

# Конфигурация для классификации
class ClassificationConfig:
    """Конфигурация для классификации различных типов сущностей."""
    
    # Настройки для подрядчиков
    CONTRACTOR = {
        "column_name": "work_types",
        "item_type": "вид работ",
        "description": "Классификация по видам работ подрядчиков"
    }
    
    # Настройки для рисков
    RISK = {
        "column_name": "project_name", 
        "item_type": "проект",
        "description": "Классификация рисков по названиям проектов"
    }
    
    # Настройки для ошибок
    ERROR = {
        "column_name": "project_name",
        "item_type": "проект", 
        "description": "Классификация ошибок по проектам"
    }
    
    # Настройки для процессов
    PROCESS = {
        "column_name": "process_name",
        "item_type": "процесс",
        "description": "Классификация по бизнес-процессам"
    }
    
    @classmethod
    def get_config(cls, entity_type: str) -> Dict[str, str]:
        """
        Получает конфигурацию классификации для указанного типа сущности.
        
        :param entity_type: Тип сущности (CONTRACTOR, RISK, ERROR, PROCESS)
        :return: Словарь с настройками классификации
        """
        config_map = {
            "CONTRACTOR": cls.CONTRACTOR,
            "RISK": cls.RISK, 
            "ERROR": cls.ERROR,
            "PROCESS": cls.PROCESS
        }
        
        return config_map.get(entity_type.upper(), {})
    
    @classmethod
    def get_all_configs(cls) -> Dict[str, Dict[str, str]]:
        """
        Возвращает все доступные конфигурации классификации.
        
        :return: Словарь всех конфигураций
        """
        return {
            "CONTRACTOR": cls.CONTRACTOR,
            "RISK": cls.RISK,
            "ERROR": cls.ERROR, 
            "PROCESS": cls.PROCESS
        }

# Глобальный экземпляр конфигурации классификации
classification_config = ClassificationConfig()

# Конфигурация для умной фильтрации
class SmartFilteringSettings(BaseSettings):
    """Настройки для этапа умной фильтрации в пайплайнах."""
    # Какому пайплайну какая СТРАТЕГИЯ соответствует
    strategy: Dict[str, str] = {
        "contractors": "none",
        "risks": "keybert",
        "errors": "none",
        "processes": "none",
    }
    
    # Какая СТРАТЕГИЯ какой ИНСТРУМЕНТ использует
    strategy_tool_map: Dict[str, str] = {
        "keybert": "search_by_keywords",
    }
    
    llm_schemas_path: str = "app/tools/llm_schemas"

# Создание экземпляра настроек умной фильтрации
smart_filtering_settings = SmartFilteringSettings()
