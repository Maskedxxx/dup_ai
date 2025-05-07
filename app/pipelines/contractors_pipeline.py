import pandas as pd
from typing import List, Dict
from app.pipelines.base import Pipeline
from app.domain.models.answer import Answer
from app.domain.models.contractor import Contractor
from app.adapters.excel_loader import ExcelLoader
from app.services.contractor_normalization import NormalizationService
from app.services.contractor_classifier import ContractorClassifierService
from app.services.contractor_answer_generator import AnswerGeneratorService
from app.domain.enums import ButtonType
from app.utils.logging import setup_logger

# Настройка логгера
logger = setup_logger(__name__)

class ContractorsPipeline(Pipeline):
    """
    Пайплайн для обработки запросов о подрядчиках.
    """
    
    def __init__(
        self,
        excel_loader: ExcelLoader,
        normalization_service: NormalizationService,
        classifier_service: ContractorClassifierService,
        answer_generator: AnswerGeneratorService
    ):
        """
        Инициализация пайплайна.
        
        :param excel_loader: Адаптер для загрузки данных из Excel
        :param normalization_service: Сервис нормализации данных
        :param classifier_service: Сервис классификации подрядчиков
        :param answer_generator: Сервис генерации ответов
        """
        self.excel_loader = excel_loader
        self.normalization_service = normalization_service
        self.classifier_service = classifier_service
        self.answer_generator = answer_generator
        logger.info("Инициализирован пайплайн для обработки запросов о подрядчиках")
    
    def process(self, question: str) -> Answer:
        """
        Обрабатывает вопрос о подрядчиках и возвращает ответ.
        
        :param question: Вопрос пользователя
        :return: Модель Answer с результатом обработки
        """
        logger.info(f"Обработка вопроса: '{question}'")
        
        try:
            # 1. Загрузка данных
            df = self.excel_loader.load(button_type=ButtonType.CONTRACTORS)

            
            # 2. Нормализация данных
            cleaned_df = self.normalization_service.clean_df(df)
            
            # 3. Загрузка типов работ
            self.classifier_service.load_work_types(cleaned_df)
            
            # 4. Классификация вопроса
            best_work_type = self.classifier_service.classify(question)
            
            # 5. Фильтрация подрядчиков
            filtered_df, relevance_scores = self.classifier_service.filter_contractors(cleaned_df, best_work_type)
            
            # 6. Преобразование в модели
            contractors = self._dataframe_to_models(filtered_df, relevance_scores)
            
            # 7. Генерация ответа
            additional_context = f"Найдено {len(filtered_df)} подрядчиков для типа работ '{best_work_type}'."
            answer = self.answer_generator.make_md(question, contractors, additional_context)
            
            logger.info(f"Успешно обработан вопрос, найдено {len(contractors)} подрядчиков")
            return answer
            
        except Exception as e:
            logger.error(f"Ошибка при обработке вопроса: {e}")
            
            # В случае ошибки возвращаем базовый ответ с информацией об ошибке
            error_answer = Answer(
                text=f"К сожалению, произошла ошибка при обработке вашего запроса: {str(e)}",
                query=question,
                total_found=0,
                items=[]
            )
            
            return error_answer
    
    def _dataframe_to_models(self, df: pd.DataFrame, relevance_scores: Dict[int, float]) -> List[Contractor]:
        """
        Преобразует DataFrame в список моделей Contractor.
        
        :param df: DataFrame с данными о подрядчиках
        :param relevance_scores: Словарь с оценками релевантности {индекс: оценка}
        :return: Список моделей Contractor
        """
        logger.debug(f"Преобразование {len(df)} записей в модели")
        
        contractors = []
        for idx, row in df.iterrows():
            try:
                contractor = Contractor(
                    name=row.get('name', ''),
                    work_types=row.get('work_types', ''),
                    contact_person=row.get('contact_person', ''),
                    contacts=row.get('contacts', ''),
                    website=row.get('website', ''),
                    projects=row.get('projects', ''),
                    comments=row.get('comments', ''),
                    primary_info=row.get('primary_info', ''),
                    staff_size=row.get('staff_size', ''),
                    relevance_score=relevance_scores.get(idx)
                )
                contractors.append(contractor)
            except Exception as e:
                logger.warning(f"Ошибка преобразования записи {idx}: {e}")
                
        # Сортируем по релевантности, если она указана
        if relevance_scores:
            contractors.sort(key=lambda x: x.relevance_score or 0, reverse=True)
            
        logger.debug(f"Преобразовано {len(contractors)} моделей")
        return contractors