# app/pipelines/base.py

import pandas as pd
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Type
from pydantic import BaseModel
from app.domain.models.answer import Answer
from app.domain.enums import ButtonType
from app.adapters.excel_loader import ExcelLoader
from app.utils.logging import setup_logger

# Настройка логгера
logger = setup_logger(__name__)


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
        logger.info(f"Инициализирован {self.__class__.__name__}")
    
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
        logger.info(f"Обработка вопроса о {entity_name}: '{question}'")
        
        try:
            # 1. Загрузка данных
            logger.debug("[1/8] Загрузка данных из Excel")
            df = self.excel_loader.load(button_type=self.button_type)
            
            # 2. Нормализация данных
            logger.debug("[2/8] Нормализация данных")
            cleaned_df = self.normalization_service.clean_df(df)
            
            # 3. Предварительная обработка (например, фильтрация по категории)
            logger.debug("[3/8] Предварительная обработка")
            processed_df = self._pre_process_dataframe(cleaned_df, **kwargs)
            
            # Проверка наличия данных после предварительной обработки
            if len(processed_df) == 0:
                logger.warning(f"Нет данных после предварительной обработки")
                return self._create_empty_answer(question, kwargs)
            
            # 4. Загрузка элементов для классификации
            logger.debug("[4/8] Загрузка элементов для классификации")
            self._load_classifier_items(processed_df)
            
            # 5. Классификация вопроса
            logger.debug("[5/8] Классификация вопроса")
            best_item = self.classifier_service.classify(question)
            
            # 6. Фильтрация данных
            logger.debug("[6/8] Фильтрация данных")
            filtered_df, relevance_scores = self._filter_data(processed_df, best_item)
            
            # 7. Преобразование в модели
            logger.debug("[7/8] Преобразование записей в модели")
            items = self._dataframe_to_models(filtered_df, relevance_scores)
            
            # 8. Генерация ответа
            logger.debug("[8/8] Генерация ответа")
            additional_context = self._generate_additional_context(filtered_df, best_item, **kwargs)
            answer = self._generate_answer(question, items, additional_context, **kwargs)
            
            logger.info(f"Успешно обработан вопрос о {entity_name}, найдено {len(items)} элементов")
            return answer
            
        except Exception as e:
            logger.error(f"Ошибка при обработке вопроса о {entity_name}: {e}")
            return self._create_error_answer(question, str(e), kwargs)
    
    def _load_classifier_items(self, df: pd.DataFrame):
        """
        Загружает элементы для классификации.
        """
        # Используем универсальный метод load_items из базового класса
        if hasattr(self.classifier_service, 'load_items'):
            self.classifier_service.load_items(df)
        else:
            # Fallback для совместимости
            logger.warning("Использование старого API классификатора")
    
    def _filter_data(self, df: pd.DataFrame, item_value: str) -> tuple:
        """
        Фильтрует данные по выбранному элементу.
        """
        # Используем универсальный метод filter_items из базового класса
        if hasattr(self.classifier_service, 'filter_items'):
            return self.classifier_service.filter_items(df, item_value)
        else:
            # Fallback для совместимости
            logger.warning("Использование старого API классификатора")
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
        logger.debug(f"Преобразование {len(df)} записей в модели {entity_name}")
        
        items = []
        for idx, row in df.iterrows():
            try:
                item = self._create_model_instance(row, relevance_scores.get(idx))
                items.append(item)
            except Exception as e:
                logger.warning(f"Ошибка преобразования записи {idx} в модель: {e}")
                
        # Сортируем по релевантности, если она указана
        if relevance_scores:
            items.sort(key=lambda x: getattr(x, 'relevance_score', 0) or 0, reverse=True)
            
        logger.debug(f"Преобразовано {len(items)} моделей {entity_name}")
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