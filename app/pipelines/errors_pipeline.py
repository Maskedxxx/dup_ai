# app/pipelines/errors_pipeline.py

import pandas as pd
from typing import List, Dict
from app.pipelines.base import Pipeline
from app.domain.models.answer import Answer
from app.domain.models.error import Error
from app.domain.enums import ButtonType
from app.adapters.excel_loader import ExcelLoader
from app.services.error_normalization import ErrorNormalizationService
from app.services.error_classifier import ErrorClassifierService
from app.services.error_answer_generator import ErrorAnswerGeneratorService
from app.utils.logging import setup_logger

# Настройка логгера
logger = setup_logger("errors_pipeline")

class ErrorsPipeline(Pipeline):
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
        Инициализация пайплайна.
        
        :param excel_loader: Адаптер для загрузки данных из Excel
        :param normalization_service: Сервис нормализации данных об ошибках
        :param classifier_service: Сервис классификации ошибок
        :param answer_generator: Сервис генерации ответов об ошибках
        """
        self.excel_loader = excel_loader
        self.normalization_service = normalization_service
        self.classifier_service = classifier_service
        self.answer_generator = answer_generator
        logger.info("Инициализирован пайплайн для обработки запросов об ошибках")
    
    def process(self, question: str) -> Answer:
        """
        Обрабатывает вопрос об ошибках и возвращает ответ.
        
        :param question: Вопрос пользователя
        :return: Модель Answer с результатом обработки
        """
        logger.info(f"Обработка вопроса об ошибках: '{question}'")
        
        try:
            # 1. Загрузка данных
            df = self.excel_loader.load(button_type=ButtonType.ERRORS)
            
            # 2. Нормализация данных
            cleaned_df = self.normalization_service.clean_df(df)
            
            # 3. Загрузка названий проектов
            self.classifier_service.load_project_names(cleaned_df)
            
            # 4. Классификация вопроса по проектам
            best_project_name = self.classifier_service.classify(question)
            
            # 5. Фильтрация ошибок по проекту
            filtered_df, relevance_scores = self.classifier_service.filter_errors(cleaned_df, best_project_name)
            
            # 6. Преобразование в модели
            errors = self._dataframe_to_models(filtered_df, relevance_scores)
            
            # 7. Генерация ответа
            additional_context = f"Найдено {len(filtered_df)} ошибок для проекта '{best_project_name}'."
            answer = self.answer_generator.make_md(question, errors, additional_context)
            
            logger.info(f"Успешно обработан вопрос об ошибках, найдено {len(errors)} ошибок")
            return answer
            
        except Exception as e:
            logger.error(f"Ошибка при обработке вопроса об ошибках: {e}")
            
            # В случае ошибки возвращаем базовый ответ с информацией об ошибке
            error_answer = Answer(
                text=f"К сожалению, произошла ошибка при обработке вашего запроса об ошибках: {str(e)}",
                query=question,
                total_found=0,
                items=[]
            )
            
            return error_answer
    
    def _dataframe_to_models(self, df: pd.DataFrame, relevance_scores: Dict[int, float]) -> List[Error]:
        """
        Преобразует DataFrame в список моделей Error.
        
        :param df: DataFrame с данными об ошибках
        :param relevance_scores: Словарь с оценками релевантности {индекс: оценка}
        :return: Список моделей Error
        """
        logger.debug(f"Преобразование {len(df)} записей в модели Error")
        
        errors = []
        for idx, row in df.iterrows():
            try:
                error = Error(
                    date=str(row.get('date', '')),
                    responsible=row.get('responsible', ''),
                    subject=row.get('subject', ''),
                    description=row.get('description', ''),
                    measures=row.get('measures', ''),
                    reason=row.get('reason', ''),
                    project=row.get('project', ''),
                    stage=row.get('stage', ''),
                    category=row.get('category', ''),
                    relevance_score=relevance_scores.get(idx)
                )
                errors.append(error)
            except Exception as e:
                logger.warning(f"Ошибка преобразования записи {idx} в модель Error: {e}")
                
        # Сортируем по релевантности, если она указана
        if relevance_scores:
            errors.sort(key=lambda x: x.relevance_score or 0, reverse=True)
            
        logger.debug(f"Преобразовано {len(errors)} моделей Error")
        return errors