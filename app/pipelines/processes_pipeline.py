# app/pipelines/processes_pipeline.py

from typing import Optional
import pandas as pd
from app.pipelines.base import BasePipeline
from app.domain.models.process import Process
from app.domain.enums import ButtonType
from app.adapters.excel_loader import ExcelLoader
from app.services.process_normalization import ProcessNormalizationService
from app.services.process_classifier import ProcessClassifierService
from app.services.process_answer_generator import ProcessAnswerGeneratorService
from app.utils.logging import setup_logger

# Настройка логгера
logger = setup_logger(__name__)


class ProcessesPipeline(BasePipeline):
    """
    Пайплайн для обработки запросов о бизнес-процессах.
    """
    
    def __init__(
        self,
        excel_loader: ExcelLoader,
        normalization_service: ProcessNormalizationService,
        classifier_service: ProcessClassifierService,
        answer_generator: ProcessAnswerGeneratorService
    ):
        """
        Инициализация пайплайна процессов.
        """
        super().__init__(
            excel_loader=excel_loader,
            normalization_service=normalization_service,
            classifier_service=classifier_service,
            answer_generator=answer_generator,
            button_type=ButtonType.PROCESSES
        )
    
    def _create_model_instance(self, row: pd.Series, relevance_score: Optional[float]) -> Process:
        """
        Создает экземпляр процесса из строки DataFrame.
        
        :param row: Строка DataFrame
        :param relevance_score: Оценка релевантности
        :return: Экземпляр Process
        """
        return Process(
            id=str(row.get('id', '')),
            name=row.get('name', ''),
            description=row.get('description', ''),
            json_file=row.get('json_file', ''),
            text_description=row.get('text_description', ''),
            relevance_score=relevance_score
        )
    
    def _get_entity_name(self) -> str:
        """
        Возвращает название сущности.
        
        :return: 'бизнес-процессов'
        """
        return "бизнес-процессов"
    
    def _load_classifier_items(self, df: pd.DataFrame):
        """
        Загружает названия процессов для классификации.
        """
        self.classifier_service.load_process_names(df)
    
    def _filter_data(self, df: pd.DataFrame, item_value: str):
        """
        Фильтрует процессы по названию.
        """
        return self.classifier_service.filter_processes(df, item_value)
    
    def _generate_additional_context(self, filtered_df: pd.DataFrame, best_item: str, **kwargs) -> str:
        """
        Генерирует контекст для процессов.
        """
        return f"Найдено {len(filtered_df)} бизнес-процессов по запросу."