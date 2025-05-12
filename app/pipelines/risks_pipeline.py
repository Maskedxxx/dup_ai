# app/pipelines/risks_pipeline.py

import pandas as pd
from typing import List, Dict
from app.pipelines.base import Pipeline
from app.domain.models.answer import Answer
from app.domain.models.risk import Risk
from app.domain.enums import RiskCategory
from app.adapters.excel_loader import ExcelLoader
from app.services.risk_normalization import RiskNormalizationService
from app.services.risk_classifier import RiskClassifierService
from app.services.risk_answer_generator import RiskAnswerGeneratorService
from app.domain.enums import ButtonType
from app.utils.logging import setup_logger

# Настройка логгера
logger = setup_logger(__name__)

class RisksPipeline(Pipeline):
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
        Инициализация пайплайна.
        
        :param excel_loader: Адаптер для загрузки данных из Excel
        :param normalization_service: Сервис нормализации данных о рисках
        :param classifier_service: Сервис классификации рисков
        :param answer_generator: Сервис генерации ответов о рисках
        """
        self.excel_loader = excel_loader
        self.normalization_service = normalization_service
        self.classifier_service = classifier_service
        self.answer_generator = answer_generator
        logger.info("Инициализирован пайплайн для обработки запросов о рисках")
    
    def process(self, question: str, risk_category: RiskCategory) -> Answer:
        """
        Обрабатывает вопрос о рисках и возвращает ответ.
        
        :param question: Вопрос пользователя
        :param risk_category: Категория риска
        :return: Модель Answer с результатом обработки
        """
        logger.info(f"Обработка вопроса о рисках: '{question}', категория: {risk_category}")
        
        try:
            # 1. Загрузка данных
            df = self.excel_loader.load(button_type=ButtonType.RISKS)
            
            # 2. Нормализация данных
            cleaned_df = self.normalization_service.clean_df(df)
            logger.info(f"Уникальные значения project_type: {cleaned_df['project_type'].unique()}")
            
            # 3. Фильтрация по категории риска
            category_value = risk_category
            logger.info(f"Фильтрация по категории: {category_value}")
            category_filtered_df = cleaned_df[cleaned_df['project_type'] == category_value]
            
            if len(category_filtered_df) == 0:
                logger.warning(f"Не найдено рисков для категории '{risk_category}'")
                return Answer(
                    text=f"По вашему запросу не найдено рисков в категории '{risk_category}'.",
                    query=question,
                    total_found=0,
                    items=[],
                    category=category_value
                )
            
            # 4. Загрузка названий проектов
            self.classifier_service.load_project_names(category_filtered_df)
            
            # 5. Классификация вопроса по проектам
            best_project_name = self.classifier_service.classify(question)
            
            # 6. Фильтрация рисков по проекту
            filtered_df, relevance_scores = self.classifier_service.filter_risks(category_filtered_df, best_project_name)
            
            # 7. Преобразование в модели
            risks = self._dataframe_to_models(filtered_df, relevance_scores)
            
            # 8. Генерация ответа
            additional_context = f"Найдено {len(filtered_df)} рисков для проекта '{best_project_name}' в категории '{category_value}'."
            answer = self.answer_generator.make_md(question, risks, category_value, additional_context)
            
            logger.info(f"Успешно обработан вопрос о рисках, найдено {len(risks)} рисков")
            return answer
            
        except Exception as e:
            logger.error(f"Ошибка при обработке вопроса о рисках: {e}")
            
            # В случае ошибки возвращаем базовый ответ с информацией об ошибке
            error_answer = Answer(
                text=f"К сожалению, произошла ошибка при обработке вашего запроса о рисках: {str(e)}",
                query=question,
                total_found=0,
                items=[],
                category=risk_category
            )
            
            return error_answer
    
    def _dataframe_to_models(self, df: pd.DataFrame, relevance_scores: Dict[int, float]) -> List[Risk]:
        """
        Преобразует DataFrame в список моделей Risk.
        
        :param df: DataFrame с данными о рисках
        :param relevance_scores: Словарь с оценками релевантности {индекс: оценка}
        :return: Список моделей Risk
        """
        logger.debug(f"Преобразование {len(df)} записей в модели Risk")
        
        risks = []
        for idx, row in df.iterrows():
            try:
                risk = Risk(
                    project_id=str(row.get('project_id', '')),
                    project_type=row.get('project_type', ''),
                    project_name=row.get('project_name', ''),
                    risk_text=row.get('risk_text', ''),
                    risk_priority=row.get('risk_priority', ''),
                    status=row.get('status', ''),
                    relevance_score=relevance_scores.get(idx)
                )
                risks.append(risk)
            except Exception as e:
                logger.warning(f"Ошибка преобразования записи {idx} в модель Risk: {e}")
                
        # Сортируем по релевантности, если она указана
        if relevance_scores:
            risks.sort(key=lambda x: x.relevance_score or 0, reverse=True)
            
        logger.debug(f"Преобразовано {len(risks)} моделей Risk")
        return risks