# app/pipelines/contractors_pipeline.py

from typing import Optional, List
import pandas as pd
from app.pipelines.base import BasePipeline
from app.domain.models.contractor import Contractor
from app.domain.enums import ButtonType
from app.adapters.excel_loader import ExcelLoader
from app.services.contractor_normalization import NormalizationService
from app.services.contractor_classifier import ContractorClassifierService
from app.services.contractor_answer_generator import AnswerGeneratorService
from app.utils.logging import setup_logger

# Настройка логгера
logger = setup_logger(__name__)


class ContractorsPipeline(BasePipeline):
    """
    Пайплайн для обработки запросов о подрядчиках.
    """
    
    def __init__(
        self,
        excel_loader: ExcelLoader,
        normalization_service: NormalizationService,
        classifier_service: ContractorClassifierService,
        answer_generator: AnswerGeneratorService,
        tool_executor # Добавляем tool_executor
    ):
        """
        Инициализация пайплайна подрядчиков.
        """
        super().__init__(
            excel_loader=excel_loader,
            normalization_service=normalization_service,
            classifier_service=classifier_service,
            answer_generator=answer_generator,
            button_type=ButtonType.CONTRACTORS,
            tool_executor=tool_executor # Передаем в родительский класс
        )
    
    def _create_model_instance(self, row: pd.Series, relevance_score: Optional[float]) -> Contractor:
        """
        Создает экземпляр подрядчика из строки DataFrame.
        
        :param row: Строка DataFrame
        :param relevance_score: Оценка релевантности
        :return: Экземпляр Contractor
        """
        return Contractor(
            name=row.get('name', ''),
            work_types=row.get('work_types', ''),
            contact_person=row.get('contact_person', ''),
            contacts=row.get('contacts', ''),
            website=row.get('website', ''),
            projects=row.get('projects', ''),
            comments=row.get('comments', ''),
            primary_info=row.get('primary_info', ''),
            staff_size=row.get('staff_size', ''),
            relevance_score=relevance_score
        )
    
    def _get_entity_name(self) -> str:
        """
        Возвращает название сущности.
        
        :return: 'подрядчиков'
        """
        return "подрядчиков"
    
    def _load_classifier_items(self, df: pd.DataFrame):
        """
        Загружает типы работ для классификации.
        Переопределяем для совместимости со старым API.
        """
        self.classifier_service.load_work_types(df)
    
    def _filter_data(self, df: pd.DataFrame, item_value: str):
        """
        Фильтрует подрядчиков по типу работ.
        Переопределяем для совместимости со старым API.
        """
        return self.classifier_service.filter_contractors(df, item_value)
    
    def _generate_additional_context(self, filtered_df: pd.DataFrame, best_item: str, **kwargs) -> str:
        """
        Генерирует контекст для подрядчиков.
        """
        return f"Найдено {len(filtered_df)} подрядчиков для типа работ '{best_item}'."