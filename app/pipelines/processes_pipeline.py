# app/pipelines/processes_pipeline.py

import pandas as pd
from typing import List, Dict
from app.pipelines.base import Pipeline
from app.domain.models.answer import Answer
from app.domain.models.process import Process
from app.domain.enums import ButtonType
from app.adapters.excel_loader import ExcelLoader
from app.services.process_normalization import ProcessNormalizationService
from app.services.process_classifier import ProcessClassifierService
from app.services.process_answer_generator import ProcessAnswerGeneratorService
from app.utils.logging import setup_logger

# Настройка логгера
logger = setup_logger("processes_pipeline")

class ProcessesPipeline(Pipeline):
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
        Инициализация пайплайна.
        """
        self.excel_loader = excel_loader
        self.normalization_service = normalization_service
        self.classifier_service = classifier_service
        self.answer_generator = answer_generator
        logger.info("Инициализирован пайплайн для обработки запросов о бизнес-процессах")
    
    def process(self, question: str) -> Answer:
        """
        Обрабатывает вопрос о бизнес-процессах и возвращает ответ.
        
        :param question: Вопрос пользователя
        :return: Модель Answer с результатом обработки
        """
        logger.info(f"Обработка вопроса о бизнес-процессах: '{question}'")
        
        try:
            # 1. Загрузка данных
            df = self.excel_loader.load(button_type=ButtonType.PROCESSES)
            
            # 2. Нормализация данных
            cleaned_df = self.normalization_service.clean_df(df)
            
            # 3. Загрузка названий процессов
            self.classifier_service.load_process_names(cleaned_df)
            
            # 4. Классификация вопроса по процессам
            best_process_name = self.classifier_service.classify(question)
            
            # 5. Фильтрация процессов
            filtered_df, relevance_scores = self.classifier_service.filter_processes(cleaned_df, best_process_name)
            
            # 6. Преобразование в модели
            processes = self._dataframe_to_models(filtered_df, relevance_scores)
            
            # 7. Генерация ответа
            additional_context = f"Найдено {len(filtered_df)} бизнес-процессов по запросу."
            answer = self.answer_generator.make_md(question, processes, additional_context)
            
            logger.info(f"Успешно обработан вопрос о бизнес-процессах, найдено {len(processes)} процессов")
            return answer
            
        except Exception as e:
            logger.error(f"Ошибка при обработке вопроса о бизнес-процессах: {e}")
            
            # В случае ошибки возвращаем базовый ответ с информацией об ошибке
            error_answer = Answer(
                text=f"К сожалению, произошла ошибка при обработке вашего запроса о бизнес-процессах: {str(e)}",
                query=question,
                total_found=0,
                items=[]
            )
            
            return error_answer
    
    def _dataframe_to_models(self, df: pd.DataFrame, relevance_scores: Dict[int, float]) -> List[Process]:
        """
        Преобразует DataFrame в список моделей Process.
        
        :param df: DataFrame с данными о бизнес-процессах
        :param relevance_scores: Словарь с оценками релевантности {индекс: оценка}
        :return: Список моделей Process
        """
        logger.debug(f"Преобразование {len(df)} записей в модели Process")
        
        processes = []
        for idx, row in df.iterrows():
            try:
                process = Process(
                    id=str(row.get('id', '')),
                    name=row.get('name', ''),
                    description=row.get('description', ''),
                    json_file=row.get('json_file', ''),
                    text_description=row.get('text_description', ''),
                    relevance_score=relevance_scores.get(idx)
                )
                processes.append(process)
            except Exception as e:
                logger.warning(f"Ошибка преобразования записи {idx} в модель Process: {e}")
                
        # Сортируем по релевантности
        if relevance_scores:
            processes.sort(key=lambda x: x.relevance_score or 0, reverse=True)
            
        logger.debug(f"Преобразовано {len(processes)} моделей Process")
        return processes