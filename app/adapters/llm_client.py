# app/adapters/llm_client.py

from openai import OpenAI
from typing import Dict, List, Any, Optional, Type, TypeVar
from pydantic import BaseModel
from app.config import llm_settings
from app.utils.logging import setup_logger

# Настройка логгера
logger = setup_logger(__name__)

T = TypeVar('T', bound=BaseModel)

class LLMClient:
    """Клиент для взаимодействия с моделями LLM."""
    
    def __init__(self):
        """Инициализация клиента LLM."""
        try:
            self.base_url = llm_settings.ollama_base_url
            self.api_key = llm_settings.ollama_api_key
            self.model_name = llm_settings.ollama_model
            
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key
            )
            
            logger.info(f"Инициализирован LLM клиент с моделью {self.model_name}")
        except Exception as e:
            logger.error(f"Ошибка инициализации LLM клиента: {e}")
            self.client = None
    
    def generate_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0
    ) -> str:
        """
        Генерирует текстовый ответ от LLM.
        
        :param system_prompt: Системный промпт
        :param user_prompt: Пользовательский промпт
        :param temperature: Температура (степень креативности)
        :return: Текстовый ответ от модели
        """
        if not self.client:
            logger.error("LLM клиент не инициализирован")
            return ""
            
        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
            )
            
            response_text = completion.choices[0].message.content
            logger.debug(f"Получен ответ от LLM: {response_text[:100]}...")
            
            return response_text
        except Exception as e:
            logger.error(f"Ошибка при генерации ответа от LLM: {e}")
            return ""
    
    def generate_structured_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
        temperature: float = 0.0
    ) -> Optional[T]:
        """
        Генерирует структурированный ответ от LLM.
        
        :param system_prompt: Системный промпт
        :param user_prompt: Пользовательский промпт
        :param response_model: Модель данных Pydantic для ответа
        :param temperature: Температура (степень креативности)
        :return: Структурированный ответ в виде модели Pydantic или None при ошибке
        """
        if not self.client:
            logger.error("LLM клиент не инициализирован")
            return None
            
        try:
            completion = self.client.beta.chat.completions.parse(
                temperature=temperature,
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format=response_model,
            )
            
            response = completion.choices[0].message
            if response.parsed:
                logger.debug("Получен структурированный ответ от LLM")
                return response.parsed
            
            logger.warning("Модель не вернула структурированный ответ")
            return None
                
        except Exception as e:
            logger.error(f"Ошибка при получении структурированного ответа от LLM: {e}")
            return None
    
    def chat_completion_with_tools(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: List[Dict[str, Any]],
        tool_choice: Optional[Dict[str, Any]] = None,
        temperature: float = 0.0
    ):
        """
        Генерирует ответ с использованием OpenAI function calling.
        
        :param system_prompt: Системный промпт
        :param user_prompt: Пользовательский промпт
        :param tools: Список доступных инструментов
        :param tool_choice: Принуждение к выбору конкретного инструмента
        :param temperature: Температура (степень креативности)
        :return: Ответ от OpenAI API
        """
        if not self.client:
            logger.error("LLM клиент не инициализирован")
            return None
            
        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                tools=tools,
                tool_choice=tool_choice,
                temperature=temperature,
            )
            
            logger.debug("Получен ответ с tool calling от LLM")
            return completion
                
        except Exception as e:
            logger.error(f"Ошибка при выполнении tool calling: {e}")
            return None
    
    def chat_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0
    ) -> str:
        """
        Синоним для generate_completion для совместимости.
        """
        return self.generate_completion(system_prompt, user_prompt, temperature)