# app/utils/prompt_builder.py

from typing import List, Dict, Any
from enum import Enum
from app.utils.logging import setup_logger
from app.config import app_settings

# Настройка отдельного логгера для промптов
logger = setup_logger(__name__)

class ItemType(Enum):
    """Типы элементов для промптов."""
    PROJECT = "проект"
    RISK = "риск"
    ERROR = "ошибка"
    PROCESS = "бизнес-процесс"
    
class PromptBuilder:
    """
    Утилита для построения промптов для LLM.
    Обобщенные методы для всех типов данных.
    """
    
    @staticmethod
    def _log_prompts(method_name: str, prompts: Dict[str, str], context: Dict[str, Any] = None):
        """
        Логирует промпты если включен соответствующий флаг.
        
        :param method_name: Название метода
        :param prompts: Словарь с промптами
        :param context: Дополнительный контекст
        """
        if not app_settings.log_prompts:
            return
            
        logger.info(f"=== {method_name} ===")
        
        if context:
            logger.info(f"Контекст: {context}")
        
        logger.info("--- SYSTEM PROMPT ---")
        logger.info(prompts.get('system', ''))
        
        logger.info("--- USER PROMPT ---")
        logger.info(prompts.get('user', ''))
        
        logger.info(f"=== END {method_name} ===")
    
    @staticmethod
    def build_classification_prompt(
        question: str, 
        items: List[str], 
        item_type: str = "проект"
    ) -> Dict[str, str]:
        """
        Строит универсальные промпты для классификации запроса.
        
        :param question: Вопрос пользователя
        :param items: Список элементов для классификации
        :param item_type: Тип элементов (проект, процесс и т.д.)
        :return: Словарь с ключами 'system' и 'user' для промптов
        """
        # Системный промпт
        system_prompt = f"""Ты эксперт по классификации запросов.
        
        Твоя задача: определить, к какому {item_type} из предоставленного списка наиболее релевантен запрос пользователя.
        
        Список возможных {item_type}ов:
        <start_enums> {', '.join(items)} <finish_enums>
        
        Проанализируй запрос и выполни следующие действия:
        1. Проведи краткое рассуждение о том, к каким {item_type}ам может относиться запрос
        2. Определи топ-3 наиболее релевантных {item_type}а и дай им оценки от 0 до 1
        
        Важно: выбирай только из предоставленного списка {item_type}ов, не добавляй свои варианты.
        КРИТИЧЕСКИ ВАЖНО: Используй ТОЧНО такие же названия как в списке, без изменений букв, пробелов или знаков!
        """
        
        # Пользовательский промпт
        example_item = items[0] if items else f"Пример {item_type}а"
        
        user_prompt = f"""
        Запрос пользователя: "{question}"
        
        Задача: определи, к какому {item_type} из списка наиболее релевантен этот запрос.
        
        Верни ответ в структурированном формате json. Например:
        
        ```json
        {{
            "reasoning": "Исходя из запроса пользователя я считаю что ... <ваши рассуждения>",
            "top_matches": [
                {{"item": "{example_item}", "score": 0.9}},
                {{"item": "{items[1] if len(items) > 1 else f'Второй {item_type}'}", "score": 0.6}},
                {{"item": "{items[2] if len(items) > 2 else f'Третий {item_type}'}", "score": 0.3}}
            ]
        }}
        ```
        
        ВАЖНО: Используй ТОЧНО такие же названия {item_type}ов как в предоставленном списке, без изменений!
        """
        
        prompts = {
            'system': system_prompt,
            'user': user_prompt
        }
        
        # Логируем промпты
        PromptBuilder._log_prompts(
            "build_classification_prompt",
            prompts,
            {
                'question': question,
                'item_type': item_type,
                'items_count': len(items)
            }
        )
        
        return prompts
    
    @staticmethod
    def build_answer_prompt(
        question: str,
        documents: List[Dict[str, Any]],
        entity_type: str = "подрядчик",
        additional_context: str = ""
    ) -> Dict[str, str]:
        """
        Строит универсальные промпты для генерации ответа.
        
        :param question: Вопрос пользователя
        :param documents: Список документов с данными
        :param entity_type: Тип сущности (подрядчик, риск, ошибка, процесс)
        :param additional_context: Дополнительный контекст
        :return: Словарь с ключами 'system' и 'user' для промптов
        """
        # Определяем контекст в зависимости от типа сущности
        contexts = {
            "подрядчик": "строительных и инженерных проектов",
            "риск": "проектов разных типов",
            "ошибка": "проектов",
            "процесс": "и BPMN"
        }
        
        context = contexts.get(entity_type, "проектов")
        
        # Системный промпт
        system_prompt = f"""Ты профессиональный аналитик по {entity_type}ам {context}.
        
        Твоя задача: дать информативный ответ на запрос пользователя о {entity_type}ах на основе предоставленных данных.
        
        Ответ должен быть:
        1. Структурированным и информативным
        2. Содержать ключевую информацию о {entity_type}ах
        3. Отформатирован в виде Markdown
        4. Включать рекомендации и выводы при необходимости
        
        Не включай в ответ информацию, которой нет в предоставленных данных.
        Если вы считаете что найденные документы не имеют отношение к вопросу и не содержат релевантную информацию для отета, то ответьте пользователю: "Извините, я затрудняюсь ответить на ваш вопрос, попробуйте позже"
        """
        
        # Форматируем документы для промпта
        formatted_docs = ""
        for i, doc in enumerate(documents, 1):
            formatted_docs += f"### {entity_type.capitalize()} {i}:\n"
            
            # Добавляем основной контент, если есть
            if isinstance(doc, dict):
                # Для словарных данных
                for key, value in doc.items():
                    if value and key != 'metadata':  # Пропускаем пустые значения и метаданные
                        formatted_key = key.replace('_', ' ').capitalize()
                        formatted_docs += f"**{formatted_key}**: {value}\n"
                
                # Добавляем метаданные, если есть
                if doc.get('metadata'):
                    for key, value in doc['metadata'].items():
                        if value:
                            formatted_key = key.replace('_', ' ').capitalize()
                            formatted_docs += f"**{formatted_key}**: {value}\n"
            else:
                # Для строковых данных
                formatted_docs += str(doc) + "\n"
            
            formatted_docs += "\n---\n\n"
        
        # Пользовательский промпт
        user_prompt = f"""
        Запрос пользователя: "{question}"
        
        {additional_context}
        
        Данные о {entity_type}ах:
        
        {formatted_docs}
        
        Сгенерируй подробный и информативный ответ на запрос пользователя, используя предоставленные данные.
        """
        
        # Добавляем специфичные инструкции в зависимости от типа
        if entity_type == "риск":
            user_prompt += "\nВключи в ответ анализ рисков, их приоритетность и статус, а также рекомендации по управлению рисками."
        elif entity_type == "ошибка":
            user_prompt += "\nВключи в ответ анализ ошибок, их причин и предпринятых мер, а также рекомендации по предотвращению подобных ошибок."
        elif entity_type == "процесс":
            user_prompt += "\nВключи в ответ анализ процессов и их описания, а также рекомендации по улучшению при необходимости."
        
        prompts = {
            'system': system_prompt,
            'user': user_prompt
        }
        
        # Логируем промпты
        PromptBuilder._log_prompts(
            "build_answer_prompt",
            prompts,
            {
                'question': question,
                'entity_type': entity_type,
                'documents_count': len(documents),
                'has_additional_context': bool(additional_context)
            }
        )
        
        return prompts
    
    # Обратная совместимость - старые методы теперь используют новые универсальные
    
    @staticmethod
    def build_contractor_classification_prompt(question: str, work_types: List[str]) -> Dict[str, str]:
        """Обратная совместимость для классификации подрядчиков."""
        return PromptBuilder.build_classification_prompt(question, work_types, "проект")
    
    @staticmethod
    def build_contractor_answer_prompt(question: str, documents: List[Dict[str, Any]], additional_context: str = "") -> Dict[str, str]:
        """Обратная совместимость для ответов о подрядчиках."""
        return PromptBuilder.build_answer_prompt(question, documents, "подрядчик", additional_context)
    
    @staticmethod
    def build_risk_project_classification_prompt(question: str, project_names: List[str]) -> Dict[str, str]:
        """Обратная совместимость для классификации рисков."""
        return PromptBuilder.build_classification_prompt(question, project_names, "проект")
    
    @staticmethod
    def build_risk_answer_prompt(question: str, risks: List[Dict[str, Any]], category: str, additional_context: str = "") -> Dict[str, str]:
        """Обратная совместимость для ответов о рисках."""
        # Добавляем категорию в контекст
        full_context = f"Категория проектов: {category}\n\n{additional_context}" if additional_context else f"Категория проектов: {category}"
        return PromptBuilder.build_answer_prompt(question, risks, "риск", full_context)
    
    @staticmethod
    def build_error_project_classification_prompt(question: str, project_names: List[str]) -> Dict[str, str]:
        """Обратная совместимость для классификации ошибок."""
        return PromptBuilder.build_classification_prompt(question, project_names, "проект")
    
    @staticmethod
    def build_error_answer_prompt(question: str, errors: List[Dict[str, Any]], additional_context: str = "") -> Dict[str, str]:
        """Обратная совместимость для ответов об ошибках."""
        return PromptBuilder.build_answer_prompt(question, errors, "ошибка", additional_context)
    
    @staticmethod
    def build_process_classification_prompt(question: str, process_names: List[str]) -> Dict[str, str]:
        """Обратная совместимость для классификации процессов."""
        return PromptBuilder.build_classification_prompt(question, process_names, "бизнес-процесс")
    
    @staticmethod
    def build_process_answer_prompt(question: str, processes: List[Dict[str, Any]], additional_context: str = "") -> Dict[str, str]:
        """Обратная совместимость для ответов о процессах."""
        return PromptBuilder.build_answer_prompt(question, processes, "процесс", additional_context)