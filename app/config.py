from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Dict, Type, Optional, Any

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
    reload: bool = True

class ContractorAnalysisSettings(BaseAppSettings):
    """Настройки сервиса анализа подрядчиков."""
    model_config = ConfigDict(
        env_prefix='CONTRACTOR_',
        extra='allow'
    )
    
    # Путь к файлу с данными о подрядчиках
    data_file_path: str
    # Максимальное количество результатов
    max_results: int = 20
    # Настройки LLM
    ollama_base_url: str
    ollama_api_key: str
    ollama_model: str

# Создание экземпляров настроек
app_settings = AppSettings()
contractor_settings = ContractorAnalysisSettings()


class RiskAnalysisSettings(BaseAppSettings):
    """Настройки сервиса анализа рисков."""
    model_config = ConfigDict(
        env_prefix='RISK_',
        extra='allow'
    )
    
    # Путь к файлу с данными о рисках
    data_file_path: str
    # Максимальное количество результатов
    max_results: int

# Создание экземпляра настроек рисков
risk_settings = RiskAnalysisSettings()

class ErrorAnalysisSettings(BaseAppSettings):
    """Настройки сервиса анализа ошибок."""
    model_config = ConfigDict(
        env_prefix='ERROR_',
        extra='allow'
    )
    
    # Путь к файлу с данными об ошибках
    data_file_path: str
    # Максимальное количество результатов
    max_results: int

# Создание экземпляра настроек ошибок
error_settings = ErrorAnalysisSettings()

class ProcessAnalysisSettings(BaseAppSettings):
    """Настройки сервиса анализа бизнес-процессов."""
    model_config = ConfigDict(
        env_prefix='PROCESS_',
        extra='allow'
    )
    
    # Путь к файлу с данными о бизнес-процессах
    data_file_path: str
    # Максимальное количество результатов
    max_results: int

# Создание экземпляра настроек процессов
process_settings = ProcessAnalysisSettings()


# DI контейнер (простая реализация)
class Container:
    """Простой контейнер для управления зависимостями."""
    def __init__(self):
        self._instances: Dict[Type, Any] = {}
    
    def register(self, cls: Type, instance: Any) -> None:
        """Регистрирует экземпляр класса в контейнере."""
        self._instances[cls] = instance
    
    def get(self, cls: Type) -> Optional[Any]:
        """Возвращает экземпляр класса из контейнера."""
        return self._instances.get(cls)

container = Container()