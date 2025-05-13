# app/pipelines/risks_pipeline.py

from typing import Optional
import pandas as pd
from app.pipelines.base import BasePipeline
from app.domain.models.risk import Risk
from app.domain.models.answer import Answer
from app.domain.enums import ButtonType, RiskCategory
from app.adapters.excel_loader import ExcelLoader
from app.services.risk_normalization import RiskNormalizationService
from app.services.risk_classifier import RiskClassifierService
from app.services.risk_answer_generator import RiskAnswerGeneratorService
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
        answer_generator: RiskAnswerGeneratorService
    ):
        """
        Инициализация пайплайна рисков.
        """
        super().__init__(
            excel_loader=excel_loader,
            normalization_service=normalization_service,
            classifier_service=classifier_service,
            answer_generator=answer_generator,
            button_type=ButtonType.RISKS
        )
    
    def _create_model_instance(self, row: pd.Series, relevance_score: Optional[float]) -> Risk:
        """
        Создает экземпляр риска из строки DataFrame.
        
        :param row: Строка DataFrame
        :param relevance_score: Оценка релевантности
        :return: Экземпляр Risk
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
        """
        Возвращает название сущности.
        
        :return: 'рисков'
        """
        return "рисков"
    
    def _pre_process_dataframe(self, df: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        Фильтрует DataFrame по категории риска.
        
        :param df: Нормализованный DataFrame
        :param kwargs: Должен содержать risk_category
        :return: Отфильтрованный DataFrame
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
        """
        return self.classifier_service.filter_risks(df, item_value)
    
    def _generate_additional_context(self, filtered_df: pd.DataFrame, best_item: str, **kwargs) -> str:
        """
        Генерирует контекст для рисков.
        """
        risk_category = kwargs.get('risk_category', '')
        return f"Найдено {len(filtered_df)} рисков для проекта '{best_item}' в категории '{risk_category}'."
    
    def _generate_answer(self, question: str, items: list, additional_context: str, **kwargs) -> Answer:
        """
        Переопределяем для передачи категории в генератор ответов.
        """
        return self.answer_generator.make_md(
            question=question,
            risks=items,  # Используем старое название параметра
            category=kwargs.get('risk_category', ''),
            additional_context=additional_context
        )
    
    def process(self, question: str, risk_category: RiskCategory) -> Answer:
        """
        Совместимость с существующим API - принимаем risk_category как отдельный параметр.
        
        :param question: Вопрос пользователя
        :param risk_category: Категория риска
        :return: Модель Answer
        """
        return super().process(question, risk_category=risk_category)