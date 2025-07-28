# app/tools/tool_selector.py

from typing import List, Dict, Any
from app.adapters.llm_client import LLMClient
from app.utils.logging import setup_logger

# Настройка логгера
logger = setup_logger(__name__)


class SimpleToolSelector:
    """
    Упрощенный селектор инструментов через OpenAI function calling.
    """
    
    def __init__(self, llm_client: LLMClient):
        """
        Инициализация селектора инструментов.
        
        :param llm_client: Клиент для взаимодействия с LLM
        """
        self.llm_client = llm_client
    
    def extract_keywords(self, question: str) -> List[str]:
        """
        Извлекает ключевые слова из вопроса пользователя через function calling.
        
        :param question: Вопрос пользователя
        :return: Список ключевых слов для фильтрации
        """
        try:
            logger.info(f"Извлечение ключевых слов для вопроса: '{question}'")
            
            # Определяем tool для OpenAI
            tools = [{
                "type": "function",
                "function": {
                    "name": "filter_risks_by_keywords",
                    "description": "Фильтрует риски проектов по ключевым словам в тексте риска",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "keywords": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Список ключевых слов для поиска в тексте рисков"
                            }
                        },
                        "required": ["keywords"],
                        "additionalProperties": False
                    },
                    "strict": True
                }
            }]
            
            # Отправляем запрос с обязательным вызовом функции
            response = self.llm_client.chat_completion_with_tools(
                system_prompt="Ты эксперт по анализу рисков проектов. Извлеки ключевые слова из вопроса пользователя для поиска релевантных рисков.",
                user_prompt=f"Вопрос: {question}",
                tools=tools,
                tool_choice={"type": "function", "function": {"name": "filter_risks_by_keywords"}}
            )
            
            # Извлекаем аргументы из tool call
            if response.choices[0].message.tool_calls:
                tool_call = response.choices[0].message.tool_calls[0]
                import json
                arguments = json.loads(tool_call.function.arguments)
                keywords = arguments.get("keywords", [])
                
                logger.info(f"Извлечены ключевые слова: {keywords}")
                return keywords
            
            # Fallback
            return self._extract_simple_keywords(question)
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении ключевых слов: {e}")
            return self._extract_simple_keywords(question)
    
    def _extract_simple_keywords(self, question: str) -> List[str]:
        """
        Простое извлечение ключевых слов без LLM (fallback).
        
        :param question: Вопрос пользователя
        :return: Список ключевых слов
        """
        # Убираем стоп-слова и короткие слова
        stop_words = {'что', 'как', 'где', 'когда', 'почему', 'какие', 'для', 'в', 'на', 'с', 'по', 'и', 'или'}
        
        words = question.lower().split()
        keywords = [word.strip('.,!?";()[]{}') for word in words 
                   if len(word) > 2 and word not in stop_words]
        
        return keywords[:3]  # Берем первые 3 значимых слова