# app/services/keybert_service.py

from typing import List, Tuple
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer
from app.utils.logging import setup_logger

# Настройка логгера
logger = setup_logger(__name__)


class KeyBERTService:
    """
    Сервис для извлечения ключевых слов из текста с использованием KeyBERT и BGE-m3 модели.
    Заменяет LLM-подход на более быстрый и эффективный метод.
    """
    
    def __init__(self):
        """
        Инициализация KeyBERT сервиса с BGE-m3 моделью.
        """
        try:
            logger.info("Инициализация KeyBERT с моделью BGE-m3...")
            
            # Загружаем модель BGE-m3 (может быть задержка при первой загрузке)
            self.model = SentenceTransformer("BAAI/bge-m3")
            self.kw_model = KeyBERT(self.model)
            
            logger.info("KeyBERT сервис успешно инициализирован")
            
        except Exception as e:
            logger.error(f"Ошибка при инициализации KeyBERT: {e}")
            raise e
    
    def extract_keywords(
        self, 
        text: str, 
        top_n: int = 7, 
        keyphrase_ngram_range: Tuple[int, int] = (1, 1)
    ) -> List[str]:
        """
        Извлекает ключевые слова из текста с помощью KeyBERT.
        
        :param text: Текст для извлечения ключевых слов
        :param top_n: Количество топ ключевых слов для возврата
        :param keyphrase_ngram_range: Диапазон n-грамм для ключевых фраз
        :return: Список ключевых слов, отсортированных по релевантности
        """
        if not text or not text.strip():
            logger.warning("Пустой текст для извлечения ключевых слов")
            return []
        
        try:
            logger.debug(f"Извлечение ключевых слов из текста: '{text[:100]}...'")
            
            # Извлекаем ключевые слова с оценками
            keywords_with_scores = self.kw_model.extract_keywords(
                text,
                keyphrase_ngram_range=keyphrase_ngram_range,
                top_n=top_n
            )
            
            # Извлекаем только ключевые слова без оценок
            keywords = [kw for kw, score in keywords_with_scores]
            
            logger.info(f"Извлечено {len(keywords)} ключевых слов: {keywords}")
            
            # Логируем детали в debug режиме
            if logger.isEnabledFor(10):  # DEBUG level
                for kw, score in keywords_with_scores:
                    logger.debug(f"Ключевое слово: {kw:<20} | Оценка: {score:.3f}")
            
            return keywords
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении ключевых слов: {e}")
            return []
    
    def extract_keywords_with_scores(
        self, 
        text: str, 
        top_n: int = 7, 
        keyphrase_ngram_range: Tuple[int, int] = (1, 1)
    ) -> List[Tuple[str, float]]:
        """
        Извлекает ключевые слова с оценками релевантности.
        
        :param text: Текст для извлечения ключевых слов
        :param top_n: Количество топ ключевых слов для возврата
        :param keyphrase_ngram_range: Диапазон n-грамм для ключевых фраз
        :return: Список кортежей (ключевое_слово, оценка)
        """
        if not text or not text.strip():
            logger.warning("Пустой текст для извлечения ключевых слов")
            return []
        
        try:
            logger.debug(f"Извлечение ключевых слов с оценками из текста: '{text[:100]}...'")
            
            keywords_with_scores = self.kw_model.extract_keywords(
                text,
                keyphrase_ngram_range=keyphrase_ngram_range,
                top_n=top_n
            )
            
            logger.info(f"Извлечено {len(keywords_with_scores)} ключевых слов с оценками")
            
            return keywords_with_scores
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении ключевых слов с оценками: {e}")
            return []


# Создаем глобальный экземпляр сервиса (singleton pattern)
_keybert_service = None

def get_keybert_service() -> KeyBERTService:
    """
    Возвращает глобальный экземпляр KeyBERT сервиса.
    Использует паттерн singleton для экономии памяти.
    """
    global _keybert_service
    if _keybert_service is None:
        _keybert_service = KeyBERTService()
    return _keybert_service