# app/pipelines/__init__.py

from typing import Dict, Type
from app.domain.enums import ButtonType, RiskCategory
from app.pipelines.base import Pipeline
from app.pipelines.contractors_pipeline import ContractorsPipeline
from app.pipelines.risks_pipeline import RisksPipeline
from app.pipelines.errors_pipeline import ErrorsPipeline
from app.pipelines.processes_pipeline import ProcessesPipeline
from app.adapters.excel_loader import ExcelLoader
from app.adapters.llm_client import LLMClient
from app.services.contractor_normalization import NormalizationService
from app.services.contractor_classifier import ContractorClassifierService
from app.services.contractor_answer_generator import AnswerGeneratorService
from app.services.risk_normalization import RiskNormalizationService
from app.services.risk_classifier import RiskClassifierService
from app.services.risk_answer_generator import RiskAnswerGeneratorService
from app.services.error_normalization import ErrorNormalizationService
from app.services.error_classifier import ErrorClassifierService
from app.services.error_answer_generator import ErrorAnswerGeneratorService
from app.pipelines.processes_pipeline import ProcessesPipeline
from app.services.process_normalization import ProcessNormalizationService
from app.services.process_classifier import ProcessClassifierService
from app.services.process_answer_generator import ProcessAnswerGeneratorService
from app.tools.tool_executor import ToolExecutor
from app.config import container
from app.utils.logging import setup_logger

# Настройка логгера
logger = setup_logger(__name__)

# Словарь соответствия типов кнопок и классов пайплайнов
BUTTON_TO_PIPELINE: Dict[ButtonType, Type[Pipeline]] = {
    ButtonType.CONTRACTORS: ContractorsPipeline,
    ButtonType.RISKS: RisksPipeline,
    ButtonType.ERRORS: ErrorsPipeline,
    ButtonType.PROCESSES: ProcessesPipeline,
}

def init_container():
    """
    Инициализирует контейнер с зависимостями.
    Регистрирует фабрики для создания сервисов.
    """
    # Регистрируем фабрики для адаптеров
    container.register_factory(ExcelLoader, lambda: ExcelLoader())
    container.register_factory(LLMClient, lambda: LLMClient())
    
    # Регистрируем фабрики для сервисов подрядчиков
    container.register_factory(
        NormalizationService, 
        lambda: NormalizationService()
    )
    container.register_factory(
        ContractorClassifierService, 
        lambda: ContractorClassifierService(container.get(LLMClient))
    )
    container.register_factory(
        AnswerGeneratorService,
        lambda: AnswerGeneratorService(container.get(LLMClient))
    )
    
    # Регистрируем фабрики для сервисов рисков
    container.register_factory(
        RiskNormalizationService,
        lambda: RiskNormalizationService()
    )
    container.register_factory(
        RiskClassifierService,
        lambda: RiskClassifierService(container.get(LLMClient))
    )
    container.register_factory(
        RiskAnswerGeneratorService,
        lambda: RiskAnswerGeneratorService(container.get(LLMClient))
    )
    
    # Регистрируем фабрики для сервисов ошибок
    container.register_factory(
        ErrorNormalizationService,
        lambda: ErrorNormalizationService()
    )
    container.register_factory(
        ErrorClassifierService,
        lambda: ErrorClassifierService(container.get(LLMClient))
    )
    container.register_factory(
        ErrorAnswerGeneratorService,
        lambda: ErrorAnswerGeneratorService(container.get(LLMClient))
    )
    
    # Регистрируем фабрики для сервисов процессов
    container.register_factory(
        ProcessNormalizationService,
        lambda: ProcessNormalizationService()
    )
    container.register_factory(
        ProcessClassifierService,
        lambda: ProcessClassifierService(container.get(LLMClient))
    )
    container.register_factory(
        ProcessAnswerGeneratorService,
        lambda: ProcessAnswerGeneratorService(container.get(LLMClient))
    )
    
    # Регистрируем фабрику для tool executor
    container.register_factory(
        ToolExecutor,
        lambda: ToolExecutor(container.get(LLMClient))
    )
    
    logger.info("Контейнер с зависимостями инициализирован")

def get_pipeline(button_type: ButtonType, risk_category: RiskCategory = None) -> Pipeline:
    """
    Создает и возвращает экземпляр пайплайна соответствующего типа.
    Использует фабричный подход для создания зависимостей.
    
    :param button_type: Тип кнопки
    :param risk_category: Категория риска (только для ButtonType.RISKS)
    :return: Экземпляр пайплайна
    """
    # Проверяем наличие типа кнопки в словаре
    if button_type not in BUTTON_TO_PIPELINE:
        logger.error(f"Тип кнопки {button_type} не поддерживается")
        raise ValueError(f"Тип кнопки {button_type} не поддерживается")
    
    # Словарь фабрик для создания пайплайнов
    pipeline_factories = {
        ButtonType.CONTRACTORS: lambda: ContractorsPipeline(
            excel_loader=container.get(ExcelLoader),
            normalization_service=container.get(NormalizationService),
            classifier_service=container.get(ContractorClassifierService),
            answer_generator=container.get(AnswerGeneratorService),
            tool_executor=container.get(ToolExecutor)
        ),
        
        ButtonType.RISKS: lambda: RisksPipeline(
            excel_loader=container.get(ExcelLoader),
            normalization_service=container.get(RiskNormalizationService),
            classifier_service=container.get(RiskClassifierService),
            answer_generator=container.get(RiskAnswerGeneratorService),
            tool_executor=container.get(ToolExecutor)
        ),
        
        ButtonType.ERRORS: lambda: ErrorsPipeline(
            excel_loader=container.get(ExcelLoader),
            normalization_service=container.get(ErrorNormalizationService),
            classifier_service=container.get(ErrorClassifierService),
            answer_generator=container.get(ErrorAnswerGeneratorService),
            tool_executor=container.get(ToolExecutor)
        ),
        
        ButtonType.PROCESSES: lambda: ProcessesPipeline(
            excel_loader=container.get(ExcelLoader),
            normalization_service=container.get(ProcessNormalizationService),
            classifier_service=container.get(ProcessClassifierService),
            answer_generator=container.get(ProcessAnswerGeneratorService),
            tool_executor=container.get(ToolExecutor)
        )
    }
    
    # Получаем фабрику и создаем пайплайн
    factory = pipeline_factories.get(button_type)
    if not factory:
        logger.error(f"Не найдена фабрика для типа {button_type}")
        raise ValueError(f"Не найдена фабрика для типа {button_type}")
    
    pipeline = factory()
    logger.info(f"Создан пайплайн для типа {button_type}")
    
    return pipeline