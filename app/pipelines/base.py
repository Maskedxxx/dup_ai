# app/pipelines/base.py

import pandas as pd
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Type
from pydantic import BaseModel
from app.domain.models.answer import Answer
from app.domain.enums import ButtonType
from app.adapters.excel_loader import ExcelLoader
from app.utils.logging import get_pipeline_logger

class Pipeline(ABC):
    """
    Абстрактный базовый класс для всех пайплайнов.
    """
    
    @abstractmethod
    def process(self, question: str, **kwargs) -> Answer:
        """
        Обрабатывает вопрос и возвращает ответ.
        
        :param question: Вопрос пользователя
        :param kwargs: Дополнительные параметры
        :return: Модель Answer с результатом обработки
        """
        pass


class BasePipeline(Pipeline):
    """
    Базовый класс с общей логикой для всех пайплайнов обработки данных.
    """
    
    def __init__(
        self,
        excel_loader: ExcelLoader,
        normalization_service,
        classifier_service,
        answer_generator,
        button_type: ButtonType
    ):
        """
        Инициализация базового пайплайна.
        
        :param excel_loader: Адаптер для загрузки данных из Excel
        :param normalization_service: Сервис нормализации данных
        :param classifier_service: Сервис классификации
        :param answer_generator: Сервис генерации ответов
        :param button_type: Тип кнопки для загрузки правильного файла
        """
        self.excel_loader = excel_loader
        self.normalization_service = normalization_service
        self.classifier_service = classifier_service
        self.answer_generator = answer_generator
        self.button_type = button_type
        
        # Инициализируем логгер пайплайна
        self.pipeline_logger = get_pipeline_logger(f"{self.__class__.__name__}")
        self.pipeline_logger.log_detail(f"Инициализирован {self.__class__.__name__}")
    
    @abstractmethod
    def _create_model_instance(self, row: pd.Series, relevance_score: Optional[float]) -> BaseModel:
        """
        Создает экземпляр модели из строки DataFrame.
        Должен быть реализован в наследниках.
        
        :param row: Строка DataFrame
        :param relevance_score: Оценка релевантности
        :return: Экземпляр модели (Contractor, Risk, Error, Process)
        """
        pass
    
    @abstractmethod
    def _get_entity_name(self) -> str:
        """
        Возвращает название сущности для логирования.
        
        :return: Название сущности (подрядчик, риск, ошибка, процесс)
        """
        pass
    
    def _pre_process_dataframe(self, df: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        Дополнительная обработка DataFrame перед классификацией.
        Может быть переопределен в наследниках.
        
        :param df: Нормализованный DataFrame
        :param kwargs: Дополнительные параметры
        :return: Обработанный DataFrame
        """
        return df
    
    def _generate_additional_context(self, filtered_df: pd.DataFrame, best_item: str, **kwargs) -> str:
        """
        Генерирует дополнительный контекст для ответа.
        Может быть переопределен в наследниках.
        
        :param filtered_df: Отфильтрованный DataFrame
        :param best_item: Выбранный элемент классификации
        :param kwargs: Дополнительные параметры
        :return: Строка дополнительного контекста
        """
        entity_name = self._get_entity_name()
        return f"Найдено {len(filtered_df)} {entity_name} для '{best_item}'."
    
    def process(self, question: str, **kwargs) -> Answer:
        """
        Обрабатывает вопрос и возвращает ответ.
        
        :param question: Вопрос пользователя
        :param kwargs: Дополнительные параметры (например, risk_category)
        :return: Модель Answer с результатом обработки
        """
        entity_name = self._get_entity_name()
        
        # Начинаем блок логирования пайплайна
        pipeline_id = self.pipeline_logger.start_pipeline_block(
            button_type=self.button_type.value,
            question=question
        )
        
        try:
            # ШАГ 1: Загрузка данных
            try:
                self.pipeline_logger.log_detail(f"Начинаем загрузку данных для типа: {self.button_type.value}")
                df = self.excel_loader.load(button_type=self.button_type)
                
                # Получаем путь к файлу для логирования
                file_path = self._get_file_path_for_logging()
                self.pipeline_logger.log_step_ok(
                    1, "Загрузка данных", 
                    f"Файл загружен: {file_path} ({len(df)} строк)"
                )
                self.pipeline_logger.log_detail(f"Колонки в файле: {list(df.columns)}")
                
            except Exception as e:
                self.pipeline_logger.log_step_error(1, "Загрузка данных", str(e))
                raise
            
            # ШАГ 2: Нормализация данных
            try:
                self.pipeline_logger.log_detail("Начинаем нормализацию данных")
                self.pipeline_logger.log_detail(f"Исходные колонки: {list(df.columns)}")
                
                cleaned_df = self.normalization_service.clean_df(df)
                
                self.pipeline_logger.log_step_ok(
                    2, "Нормализация данных",
                    f"Нормализовано {len(cleaned_df)} строк, колонки: {list(cleaned_df.columns)}"
                )
                self.pipeline_logger.log_detail(f"Финальные колонки: {list(cleaned_df.columns)}")
                
            except Exception as e:
                self.pipeline_logger.log_step_error(2, "Нормализация данных", str(e))
                raise
            
            # ШАГ 3: Предварительная обработка
            try:
                self.pipeline_logger.log_detail(f"Начинаем предварительную обработку с параметрами: {kwargs}")
                processed_df = self._pre_process_dataframe(cleaned_df, **kwargs)
                
                if len(processed_df) == 0:
                    self.pipeline_logger.log_detail("Нет данных после предварительной обработки")
                    answer = self._create_empty_answer(question, kwargs)
                    self.pipeline_logger.end_pipeline_block(success=True)
                    return answer
                
                self.pipeline_logger.log_step_ok(
                    3, "Предварительная обработка",
                    f"Обработано {len(processed_df)} строк"
                )
                
            except Exception as e:
                self.pipeline_logger.log_step_error(3, "Предварительная обработка", str(e))
                raise
            
            # ШАГ 4: Загрузка элементов для классификации
            try:
                self.pipeline_logger.log_detail("Загружаем элементы для классификации")
                self._load_classifier_items(processed_df)
                
                items_count = len(self.classifier_service.items_list)
                self.pipeline_logger.log_step_ok(
                    4, "Загрузка элементов",
                    f"Загружено {items_count} уникальных элементов"
                )
                self.pipeline_logger.log_detail(f"Элементы: {self.classifier_service.items_list[:5]}...")  # Первые 5
                
            except Exception as e:
                self.pipeline_logger.log_step_error(4, "Загрузка элементов", str(e))
                raise
            
            # ШАГ 5: Классификация вопроса
            try:
                self.pipeline_logger.log_detail(f"Начинаем классификацию вопроса: '{question}'")
                best_item = self.classifier_service.classify(question)
                
                if not best_item:
                    self.pipeline_logger.log_detail("Классификация не дала результата")
                    answer = self._create_empty_answer(question, kwargs)
                    self.pipeline_logger.end_pipeline_block(success=True)
                    return answer
                
                self.pipeline_logger.log_step_ok(
                    5, "Классификация",
                    f"Выбран элемент: '{best_item}'"
                )
                
            except Exception as e:
                self.pipeline_logger.log_step_error(5, "Классификация", str(e))
                raise
            
            # ШАГ 6: Фильтрация данных
            try:
                self.pipeline_logger.log_detail(f"Фильтруем данные по элементу: '{best_item}'")
                filtered_df, relevance_scores = self._filter_data(processed_df, best_item)
                
                self.pipeline_logger.log_step_ok(
                    6, "Фильтрация данных",
                    f"Найдено {len(filtered_df)} подходящих записей"
                )
                self.pipeline_logger.log_detail(f"Индексы отфильтрованных записей: {list(filtered_df.index)}")
                
            except Exception as e:
                self.pipeline_logger.log_step_error(6, "Фильтрация данных", str(e))
                raise
            
            # ШАГ 7: Преобразование в модели
            try:
                self.pipeline_logger.log_detail("Преобразуем данные в модели")
                items = self._dataframe_to_models(filtered_df, relevance_scores)
                
                self.pipeline_logger.log_step_ok(
                    7, "Преобразование в модели",
                    f"Создано {len(items)} моделей"
                )
                
            except Exception as e:
                self.pipeline_logger.log_step_error(7, "Преобразование в модели", str(e))
                raise
            
            # ШАГ 8: Генерация ответа
            try:
                self.pipeline_logger.log_detail("Генерируем финальный ответ")
                additional_context = self._generate_additional_context(filtered_df, best_item, **kwargs)
                answer = self._generate_answer(question, items, additional_context, **kwargs)
                
                self.pipeline_logger.log_step_ok(
                    8, "Генерация ответа",
                    f"Ответ сгенерирован ({len(answer.text)} символов)"
                )
                
            except Exception as e:
                self.pipeline_logger.log_step_error(8, "Генерация ответа", str(e))
                raise
            
            # Успешное завершение
            self.pipeline_logger.log_detail(f"Пайплайн завершен успешно, найдено {len(items)} элементов")
            self.pipeline_logger.end_pipeline_block(success=True)
            return answer
            
        except Exception as e:
            # Ошибка в пайплайне
            self.pipeline_logger.log_detail(f"Критическая ошибка в пайплайне: {e}")
            self.pipeline_logger.end_pipeline_block(success=False, error_msg=str(e))
            return self._create_error_answer(question, str(e), kwargs)
    
    def _get_file_path_for_logging(self) -> str:
        """
        Получает путь к файлу для логирования.
        
        :return: Путь к файлу данных
        """
        from app.config import contractor_settings, risk_settings, error_settings, process_settings
        
        file_paths = {
            ButtonType.CONTRACTORS: contractor_settings.data_file_path,
            ButtonType.RISKS: risk_settings.data_file_path,
            ButtonType.ERRORS: error_settings.data_file_path,
            ButtonType.PROCESSES: process_settings.data_file_path,
        }
        
        return file_paths.get(self.button_type, "unknown_file")
    
    def _load_classifier_items(self, df: pd.DataFrame):
        """
        Загружает элементы для классификации.
        """
        # Используем универсальный метод load_items из базового класса
        if hasattr(self.classifier_service, 'load_items'):
            self.classifier_service.load_items(df)
        else:
            # Fallback для совместимости
            self.pipeline_logger.log_detail("Использование старого API классификатора", "WARNING")
    
    def _filter_data(self, df: pd.DataFrame, item_value: str) -> tuple:
        """
        Фильтрует данные по выбранному элементу.
        """
        # Используем универсальный метод filter_items из базового класса
        if hasattr(self.classifier_service, 'filter_items'):
            return self.classifier_service.filter_items(df, item_value)
        else:
            # Fallback для совместимости
            self.pipeline_logger.log_detail("Использование старого API классификатора", "WARNING")
            return df, {}
    
    def _generate_answer(self, question: str, items: List[BaseModel], additional_context: str, **kwargs) -> Answer:
        """
        Генерирует ответ с помощью генератора ответов.
        """
        return self.answer_generator.make_md(
            question=question,
            items=items,
            additional_context=additional_context,
            **kwargs
        )
    
    def _dataframe_to_models(self, df: pd.DataFrame, relevance_scores: Dict[int, float]) -> List[BaseModel]:
        """
        Преобразует DataFrame в список моделей.
        
        :param df: DataFrame с данными
        :param relevance_scores: Словарь с оценками релевантности
        :return: Список моделей
        """
        entity_name = self._get_entity_name()
        self.pipeline_logger.log_detail(f"Преобразование {len(df)} записей в модели {entity_name}")
        
        items = []
        for idx, row in df.iterrows():
            try:
                item = self._create_model_instance(row, relevance_scores.get(idx))
                items.append(item)
            except Exception as e:
                self.pipeline_logger.log_detail(f"Ошибка преобразования записи {idx} в модель: {e}", "WARNING")
                
        # Сортируем по релевантности, если она указана
        if relevance_scores:
            items.sort(key=lambda x: getattr(x, 'relevance_score', 0) or 0, reverse=True)
            
        self.pipeline_logger.log_detail(f"Преобразовано {len(items)} моделей {entity_name}")
        return items
    
    def _create_empty_answer(self, question: str, kwargs: dict) -> Answer:
        """
        Создает пустой ответ когда нет данных.
        """
        entity_name = self._get_entity_name()
        text = f"По вашему запросу не найдено {entity_name}."
        
        return Answer(
            text=text,
            query=question,
            total_found=0,
            items=[],
            category=kwargs.get('category')
        )
    
    def _create_error_answer(self, question: str, error_msg: str, kwargs: dict) -> Answer:
        """
        Создает ответ с информацией об ошибке.
        """
        entity_name = self._get_entity_name()
        text = f"К сожалению, произошла ошибка при обработке вашего запроса о {entity_name}: {error_msg}"
        
        return Answer(
            text=text,
            query=question,
            total_found=0,
            items=[],
            category=kwargs.get('category')
        )