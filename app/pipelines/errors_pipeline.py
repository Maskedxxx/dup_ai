# app/pipelines/errors_pipeline.py

from typing import Optional, List
import pandas as pd
from app.pipelines.base import BasePipeline
from app.tools.common_toolsets import CommonToolSets
from app.domain.models.error import Error
from app.domain.enums import ButtonType
from app.adapters.excel_loader import ExcelLoader
from app.services.error_normalization import ErrorNormalizationService
from app.services.error_classifier import ErrorClassifierService
from app.services.error_answer_generator import ErrorAnswerGeneratorService
from app.utils.logging import setup_logger

# Настройка логгера
logger = setup_logger(__name__)


class ErrorsPipeline(BasePipeline):
    """
    Пайплайн для обработки запросов об ошибках проектов.
    """
    
    def __init__(
        self,
        excel_loader: ExcelLoader,
        normalization_service: ErrorNormalizationService,
        classifier_service: ErrorClassifierService,
        answer_generator: ErrorAnswerGeneratorService
    ):
        """
        Инициализация пайплайна ошибок.
        """
        super().__init__(
            excel_loader=excel_loader,
            normalization_service=normalization_service,
            classifier_service=classifier_service,
            answer_generator=answer_generator,
            button_type=ButtonType.ERRORS
        )
    
    def _create_model_instance(self, row: pd.Series, relevance_score: Optional[float]) -> Error:
        """
        Создает экземпляр ошибки из строки DataFrame.
        
        :param row: Строка DataFrame
        :param relevance_score: Оценка релевантности
        :return: Экземпляр Error
        """
        return Error(
            date=str(row.get('date', '')),
            responsible=row.get('responsible', ''),
            subject=row.get('subject', ''),
            description=row.get('description', ''),
            measures=row.get('measures', ''),
            reason=row.get('reason', ''),
            project=row.get('project', ''),
            stage=row.get('stage', ''),
            category=row.get('category', ''),
            relevance_score=relevance_score
        )
    
    def _get_entity_name(self) -> str:
        """
        Возвращает название сущности.
        
        :return: 'ошибок'
        """
        return "ошибок"
    
    def get_tool_names(self) -> List[str]:
        """
        Возвращает набор инструментов для анализа ошибок.
        
        ПОКА ПУСТОЙ СПИСОК - инструменты для ошибок еще не созданы.
        Когда будете готовы добавить инструменты, просто раскомментируйте строку ниже:
        # return CommonToolSets.ERROR_ANALYSIS
        """
        return CommonToolSets.NONE  # Пустой список
    
    def _load_classifier_items(self, df: pd.DataFrame):
        """
        Загружает названия проектов для классификации.
        """
        self.classifier_service.load_project_names(df)
    
    def _filter_data(self, df: pd.DataFrame, item_value: str):
        """
        Фильтрует ошибки по проекту.
        """
        return self.classifier_service.filter_errors(df, item_value)
    
    def _generate_additional_context(self, filtered_df: pd.DataFrame, best_item: str, **kwargs) -> str:
        """
        Генерирует контекст для ошибок.
        """
        return f"Найдено {len(filtered_df)} ошибок для проекта '{best_item}'."