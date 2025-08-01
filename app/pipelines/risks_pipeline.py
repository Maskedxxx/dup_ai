# app/pipelines/risks_pipeline.py

from typing import Optional, List
import pandas as pd
from app.pipelines.base import BasePipeline
from app.tools.common_toolsets import CommonToolSets
from app.domain.models.risk import Risk
from app.domain.models.answer import Answer
from app.domain.enums import ButtonType, RiskCategory
from app.adapters.excel_loader import ExcelLoader
from app.services.risk_normalization import RiskNormalizationService
from app.services.risk_classifier import RiskClassifierService
from app.services.risk_answer_generator import RiskAnswerGeneratorService
from app.tools.tool_executor import ToolExecutor
from app.utils.logging import setup_logger

# Настройка логгера
logger = setup_logger(__name__)


class RisksPipeline(BasePipeline):
    """
    Пайплайн для обработки запросов о рисках проектов.
    """
    
    def __init__(
        self,
        excel_loader: ExcelLoader,
        normalization_service: RiskNormalizationService,
        classifier_service: RiskClassifierService,
        answer_generator: RiskAnswerGeneratorService,
        tool_executor: ToolExecutor  # Заменили tool_selector на tool_executor
    ):
        """
        Инициализация пайплайна рисков.
        """
        super().__init__(
            excel_loader=excel_loader,
            normalization_service=normalization_service,
            classifier_service=classifier_service,
            answer_generator=answer_generator,
            button_type=ButtonType.RISKS,
            tool_executor=tool_executor
        )
    
    def _create_model_instance(self, row: pd.Series, relevance_score: Optional[float]) -> Risk:
        """
        Создает экземпляр риска из строки DataFrame.
        """
        return Risk(
            project_id=str(row.get('project_id', '')),
            project_type=row.get('project_type', ''),
            project_name=row.get('project_name', ''),
            risk_text=row.get('risk_text', ''),
            risk_priority=row.get('risk_priority', ''),
            status=row.get('status', ''),
            relevance_score=relevance_score
        )
    
    def _get_entity_name(self) -> str:
        return "рисков"
    
    def get_tool_names(self) -> List[str]:
        """
        Возвращает набор инструментов для анализа рисков.
        
        Риски используют расширенный набор инструментов:
        - Поиск по ключевым словам
        - Фильтрация по приоритету (в будущем)
        - Фильтрация по датам (в будущем)
        """
        return CommonToolSets.RISK_ANALYSIS
    
    def _pre_process_dataframe(self, df: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        Фильтрует DataFrame по категории риска.
        """
        risk_category = kwargs.get('risk_category')
        
        if not risk_category:
            logger.warning("Не указана категория риска")
            return df
        
        logger.info(f"Фильтрация по категории: {risk_category}")
        category_filtered_df = df[df['project_type'] == risk_category]
        
        if len(category_filtered_df) == 0:
            logger.warning(f"Не найдено рисков для категории '{risk_category}'")
        
        return category_filtered_df
    
    def _load_classifier_items(self, df: pd.DataFrame):
        """
        Загружает названия проектов для классификации.
        """
        self.classifier_service.load_project_names(df)
    
    def _filter_data(self, df: pd.DataFrame, item_value: str):
        """
        Фильтрует риски по проекту.
        Логика интеллектуальной фильтрации теперь находится в BasePipeline.
        """
        return self.classifier_service.filter_risks(df, item_value)
    
    def _generate_additional_context(self, filtered_df: pd.DataFrame, best_item: str, **kwargs) -> str:
        risk_category = kwargs.get('risk_category', '')
        return f"Найдено {len(filtered_df)} рисков для проекта '{best_item}' в категории '{risk_category}'."
    
    def _generate_answer(self, question: str, items: list, additional_context: str, **kwargs) -> Answer:
        return self.answer_generator.make_md(
            question=question,
            risks=items,
            category=kwargs.get('risk_category', ''),
            additional_context=additional_context
        )
    
    def process(self, question: str, risk_category: RiskCategory) -> Answer:
        """
        Основной метод обработки, адаптированный для новой архитектуры.
        """
        # Просто вызываем родительский метод, передавая risk_category в kwargs
        return super().process(question, risk_category=risk_category.value)
