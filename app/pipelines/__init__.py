from typing import Dict, Type
from app.domain.enums import ButtonType, RiskCategory
from app.pipelines.base import Pipeline
from app.pipelines.contractors_pipeline import ContractorsPipeline
from app.pipelines.risks_pipeline import RisksPipeline
from app.pipelines.errors_pipeline import ErrorsPipeline
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
    """
    # Создаем экземпляры адаптеров
    excel_loader = ExcelLoader()
    llm_client = LLMClient()
    
    # Создаем экземпляры сервисов для подрядчиков
    normalization_service = NormalizationService()
    classifier_service = ContractorClassifierService(llm_client)
    answer_generator = AnswerGeneratorService(llm_client)
    
    # Создаем экземпляры сервисов для рисков
    risk_normalization_service = RiskNormalizationService()
    risk_classifier_service = RiskClassifierService(llm_client)
    risk_answer_generator = RiskAnswerGeneratorService(llm_client)
    
    # Создаем экземпляры сервисов для ошибок
    error_normalization_service = ErrorNormalizationService()
    error_classifier_service = ErrorClassifierService(llm_client)
    error_answer_generator = ErrorAnswerGeneratorService(llm_client)
    
    # Создаем экземпляры сервисов для бизнес-процессов
    process_normalization_service = ProcessNormalizationService()
    process_classifier_service = ProcessClassifierService(llm_client)
    process_answer_generator = ProcessAnswerGeneratorService(llm_client)
    
    # Регистрируем в контейнере
    container.register(ExcelLoader, excel_loader)
    container.register(LLMClient, llm_client)
    
    # Сервисы для подрядчиков
    container.register(NormalizationService, normalization_service)
    container.register(ContractorClassifierService, classifier_service)
    container.register(AnswerGeneratorService, answer_generator)
    
    # Сервисы для рисков
    container.register(RiskNormalizationService, risk_normalization_service)
    container.register(RiskClassifierService, risk_classifier_service)
    container.register(RiskAnswerGeneratorService, risk_answer_generator)
    
    # Сервисы для ошибок
    container.register(ErrorNormalizationService, error_normalization_service)
    container.register(ErrorClassifierService, error_classifier_service)
    container.register(ErrorAnswerGeneratorService, error_answer_generator)
    
    # сервисы для бизнес-процессов
    container.register(ProcessNormalizationService, process_normalization_service)
    container.register(ProcessClassifierService, process_classifier_service)
    container.register(ProcessAnswerGeneratorService, process_answer_generator)
    
    logger.info("Контейнер с зависимостями инициализирован")

def get_pipeline(button_type: ButtonType, risk_category: RiskCategory = None) -> Pipeline:
    """
    Создает и возвращает экземпляр пайплайна соответствующего типа.
    
    :param button_type: Тип кнопки
    :param risk_category: Категория риска (только для ButtonType.RISKS)
    :return: Экземпляр пайплайна
    """
    # Проверяем наличие типа кнопки в словаре
    if button_type not in BUTTON_TO_PIPELINE:
        logger.error(f"Тип кнопки {button_type} не поддерживается")
        raise ValueError(f"Тип кнопки {button_type} не поддерживается")
    
    # Получаем класс пайплайна
    pipeline_class = BUTTON_TO_PIPELINE[button_type]
    
    # Создаем экземпляр пайплайна с зависимостями из контейнера
    if pipeline_class == ContractorsPipeline:
        return ContractorsPipeline(
            excel_loader=container.get(ExcelLoader),
            normalization_service=container.get(NormalizationService),
            classifier_service=container.get(ContractorClassifierService),
            answer_generator=container.get(AnswerGeneratorService)
        )
        
    elif pipeline_class == RisksPipeline:
        if not risk_category:
            logger.error("Не указана категория риска для пайплайна рисков")
            raise ValueError("Не указана категория риска для пайплайна рисков")
        
        return RisksPipeline(
            excel_loader=container.get(ExcelLoader),
            normalization_service=container.get(RiskNormalizationService),
            classifier_service=container.get(RiskClassifierService),
            answer_generator=container.get(RiskAnswerGeneratorService)
        )
        
    elif pipeline_class == ErrorsPipeline:
        return ErrorsPipeline(
            excel_loader=container.get(ExcelLoader),
            normalization_service=container.get(ErrorNormalizationService),
            classifier_service=container.get(ErrorClassifierService),
            answer_generator=container.get(ErrorAnswerGeneratorService)
        )
        
    elif pipeline_class == ProcessesPipeline:
        return ProcessesPipeline(
            excel_loader=container.get(ExcelLoader),
            normalization_service=container.get(ProcessNormalizationService),
            classifier_service=container.get(ProcessClassifierService),
            answer_generator=container.get(ProcessAnswerGeneratorService)
        )
    
    # Если тип неизвестен, возвращаем ошибку
    logger.error(f"Не удалось создать пайплайн для типа {button_type}")
    raise ValueError(f"Не удалось создать пайплайн для типа {button_type}")