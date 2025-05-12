# app/utils/prompt_builder.py

from typing import List, Dict, Any

class PromptBuilder:
    """
    Утилита для построения промптов для LLM.
    """
    
    @staticmethod
    def build_classification_prompt(question: str, work_types: List[str]) -> Dict[str, str]:
        """
        Строит системный и пользовательский промпты для классификации запроса.
        
        :param question: Вопрос пользователя
        :param work_types: Список типов работ
        :return: Словарь с ключами 'system' и 'user' для промптов
        """
        # Системный промпт
        system_prompt = f"""Ты эксперт по классификации запросов в участии подрядчиков в проектах.
        
        Твоя задача: определить, к какому проекту из предоставленного списка наиболее релевантен запрос пользователя.
        
        Список возможных проектов:
        {', '.join(work_types)}
        
        Проанализируй запрос и выполни следующие действия:
        1. Проведи краткое рассуждение о том, к каким проектам может относиться запрос
        2. Определи топ-3 наиболее релевантных проекта и дай им оценки от 0 до 1
        
        Важно: выбирай только из предоставленного списка проектов, не добавляй свои варианты.
        """
        
        # Пользовательский промпт
        example_project = work_types[0] if work_types else "Бетонные конструкции"
        
        user_prompt = f"""
        Запрос пользователя: "{question}"
        
        Определи, к какому проекту из списка наиболее релевантен этот запрос.
        
        Верни ответ в структурированном формате. Например:
        
        ```json
        {{
            "reasoning": "Запрос касается установки и подключения электрооборудования в здании",
            "top_projects": {{
                "{example_project}": 0.9,
                "{work_types[1] if len(work_types) > 1 else 'Инженерные системы'}": 0.6,
                "{work_types[2] if len(work_types) > 2 else 'Проектирование зданий'}": 0.3
            }}
        }}
        ```
        """
        
        return {
            'system': system_prompt,
            'user': user_prompt
        }
    
    @staticmethod
    def build_answer_prompt(question: str, documents: List[Dict[str, Any]], additional_context: str = "") -> Dict[str, str]:
        """
        Строит системный и пользовательский промпты для генерации ответа.
        
        :param question: Вопрос пользователя
        :param documents: Список документов с данными о подрядчиках
        :param additional_context: Дополнительный контекст
        :return: Словарь с ключами 'system' и 'user' для промптов
        """
        # Системный промпт
        system_prompt = """Ты профессиональный аналитик по подбору подрядчиков для строительных и инженерных проектов.
        
        Твоя задача: дать информативный ответ на запрос пользователя о подрядчиках на основе предоставленных данных.
        
        Ответ должен быть:
        1. Структурированным и информативным
        2. Содержать ключевую информацию о подрядчиках
        3. Отформатирован в виде Markdown
        4. Включать рекомендации при необходимости
        
        Не включай в ответ информацию, которой нет в предоставленных данных.
        """
        
        # Форматируем документы для промпта
        formatted_docs = ""
        for i, doc in enumerate(documents, 1):
            formatted_docs += f"### Подрядчик {i}:\n"
            formatted_docs += f"{doc['content']}\n"
            
            # Добавляем метаданные
            if doc.get('metadata'):
                for key, value in doc['metadata'].items():
                    if value:
                        formatted_docs += f"{key}: {value}\n"
            
            formatted_docs += "\n---\n\n"
        
        # Пользовательский промпт
        user_prompt = f"""
        Запрос пользователя: "{question}"
        
        Дополнительный контекст: {additional_context}
        
        Данные о подрядчиках:
        
        {formatted_docs}
        
        Сгенерируй подробный и информативный ответ на запрос пользователя, используя предоставленные данные.
        """
        
        return {
            'system': system_prompt,
            'user': user_prompt
        }
        
        
    @staticmethod
    def build_risk_project_classification_prompt(question: str, project_names: List[str]) -> Dict[str, str]:
        """
        Строит системный и пользовательский промпты для классификации запроса о рисках по проектам.
        
        :param question: Вопрос пользователя
        :param project_names: Список названий проектов
        :return: Словарь с ключами 'system' и 'user' для промптов
        """
        # Системный промпт
        system_prompt = f"""Ты эксперт по классификации запросов о рисках в проектах.
        
        Твоя задача: определить, к какому проекту из предоставленного списка наиболее релевантен запрос пользователя о рисках.
        
        Список возможных проектов:
        {', '.join(project_names)}
        
        Проанализируй запрос и выполни следующие действия:
        1. Проведи краткое рассуждение о том, к каким проектам может относиться запрос
        2. Определи топ-3 наиболее релевантных проекта и дай им оценки от 0 до 1.
        
        Примечания:
        1. Имена проектов находятся строго в синтаксисе '<имя_проекта_1>', '<имя_проекта_2>' ..."
        2. Выбрать в топ-3 следует только по одному проекту из списка
        3. Не изменяйте орфографию имен проектов при выборе топ проектов.
        
        
        Важно: выбирай только из предоставленного списка проектов, не добавляй свои варианты.
        """
        
        # Пользовательский промпт
        example_project = "Проект разработки ПО"
        
        user_prompt = f"""
        Запрос пользователя о рисках: "{question}"
        
        Определи, к какому проекту из списка наиболее релевантен этот запрос.
        
        Верни ответ в структурированном формате. Например:
        
        ```json
        {{
            "reasoning": "Запрос касается рисков при проведении испытаний новых компонентов",
            "top_projects": {{
                "{example_project}": 0.9,
                "{project_names[1] if len(project_names) > 1 else 'Проект строительства'}": 0.6,
                "{project_names[2] if len(project_names) > 2 else 'Проект внедрения'}": 0.3
            }}
        }}
        ```
        """
        
        return {
            'system': system_prompt,
            'user': user_prompt
        }

    @staticmethod
    def build_risk_answer_prompt(question: str, risks: List[Dict[str, Any]], category: str, additional_context: str = "") -> Dict[str, str]:
        """
        Строит системный и пользовательский промпты для генерации ответа о рисках.
        
        :param question: Вопрос пользователя
        :param risks: Список рисков
        :param category: Категория риска
        :param additional_context: Дополнительный контекст
        :return: Словарь с ключами 'system' и 'user' для промптов
        """
        # Системный промпт
        system_prompt = """Ты эксперт по анализу рисков в проектах разных типов.
        
        Твоя задача: дать информативный ответ на запрос пользователя о рисках проектов на основе предоставленных данных.
        
        Ответ должен быть:
        1. Структурированным и информативным
        2. Содержать ключевую информацию о рисках и проектах
        3. Отформатирован в виде Markdown
        4. Включать рекомендации и выводы при необходимости
        
        Не включай в ответ информацию, которой нет в предоставленных данных.
        """
        
        # Форматируем данные о рисках для промпта
        formatted_risks = ""
        for i, risk in enumerate(risks, 1):
            formatted_risks += f"### Риск {i}:\n"
            formatted_risks += f"**Проект**: {risk.get('project_name', '')}\n"
            formatted_risks += f"**Описание риска**: {risk.get('risk_text', '')}\n"
            
            # Добавляем дополнительные поля, если они есть
            if risk.get('risk_priority'):
                formatted_risks += f"**Приоритет**: {risk.get('risk_priority')}\n"
            if risk.get('status'):
                formatted_risks += f"**Статус**: {risk.get('status')}\n"
            
            formatted_risks += "\n---\n\n"
        
        # Соответствие категорий
        category_names = {
            "niokr": "НИОКР (научно-исследовательские и опытно-конструкторские работы)",
            "product_project": "Продуктовые проекты",
            "manufacturing": "Производство"
        }
        
        category_name = category_names.get(category, category)
        
        # Пользовательский промпт
        user_prompt = f"""
        Запрос пользователя: "{question}"
        
        Категория проектов: {category_name}
        
        {additional_context}
        
        Данные о рисках:
        
        {formatted_risks}
        
        Сгенерируй подробный и информативный ответ на запрос пользователя, используя предоставленные данные о рисках.
        Включи в ответ анализ рисков, их приоритетность и статус, а также рекомендации по управлению рисками, если возможно.
        """
        
        return {
            'system': system_prompt,
            'user': user_prompt
        }
        
        
    @staticmethod
    def build_error_project_classification_prompt(question: str, project_names: List[str]) -> Dict[str, str]:
        """
        Строит системный и пользовательский промпты для классификации запроса об ошибках по проектам.
        
        :param question: Вопрос пользователя
        :param project_names: Список названий проектов
        :return: Словарь с ключами 'system' и 'user' для промптов
        """
        # Системный промпт
        system_prompt = f"""Ты эксперт по классификации запросов об ошибках в проектах.
        
        Твоя задача: определить, к какому проекту из предоставленного списка наиболее релевантен запрос пользователя об ошибках.
        
        Список возможных проектов:
        {', '.join(project_names)}
        
        Проанализируй запрос и выполни следующие действия:
        1. Проведи краткое рассуждение о том, к каким проектам может относиться запрос
        2. Определи топ-3 наиболее релевантных проекта и дай им оценки от 0 до 1
        
        Важно: выбирай только из предоставленного списка проектов, не добавляй свои варианты.
        """
        
        # Пользовательский промпт
        example_project = project_names[0] if project_names else "Проект A"
        
        user_prompt = f"""
        Запрос пользователя об ошибках: "{question}"
        
        Определи, к какому проекту из списка наиболее релевантен этот запрос.
        
        Верни ответ в структурированном формате. Например:
        
        ```json
        {{
            "reasoning": "Запрос касается ошибок при разработке интерфейса",
            "top_projects": {{
                "{example_project}": 0.9,
                "{project_names[1] if len(project_names) > 1 else 'Проект B'}": 0.6,
                "{project_names[2] if len(project_names) > 2 else 'Проект C'}": 0.3
            }}
        }}
        ```
        """
        
        return {
            'system': system_prompt,
            'user': user_prompt
        }

    @staticmethod
    def build_error_answer_prompt(question: str, errors: List[Dict[str, Any]], additional_context: str = "") -> Dict[str, str]:
        """
        Строит системный и пользовательский промпты для генерации ответа об ошибках.
        
        :param question: Вопрос пользователя
        :param errors: Список ошибок
        :param additional_context: Дополнительный контекст
        :return: Словарь с ключами 'system' и 'user' для промптов
        """
        # Системный промпт
        system_prompt = """Ты эксперт по анализу ошибок в проектах.
        
        Твоя задача: дать информативный ответ на запрос пользователя об ошибках проектов на основе предоставленных данных.
        
        Ответ должен быть:
        1. Структурированным и информативным
        2. Содержать ключевую информацию об ошибках и их причинах
        3. Отформатирован в виде Markdown
        4. Включать рекомендации по предотвращению подобных ошибок
        
        Не включай в ответ информацию, которой нет в предоставленных данных.
        """
        
        # Форматируем данные об ошибках для промпта
        formatted_errors = ""
        for i, error in enumerate(errors, 1):
            formatted_errors += f"### Ошибка {i}:\n"
            formatted_errors += f"**Проект**: {error.get('project', '')}\n"
            
            if error.get('date'):
                formatted_errors += f"**Дата**: {error.get('date')}\n"
            
            if error.get('subject'):
                formatted_errors += f"**Предмет ошибки**: {error.get('subject')}\n"
                
            formatted_errors += f"**Описание**: {error.get('description', '')}\n"
            
            if error.get('measures'):
                formatted_errors += f"**Предпринятые меры**: {error.get('measures')}\n"
                
            if error.get('reason'):
                formatted_errors += f"**Причина**: {error.get('reason')}\n"
                
            if error.get('stage'):
                formatted_errors += f"**Стадия проекта**: {error.get('stage')}\n"
                
            if error.get('category'):
                formatted_errors += f"**Категория**: {error.get('category')}\n"
            
            formatted_errors += "\n---\n\n"
        
        # Пользовательский промпт
        user_prompt = f"""
        Запрос пользователя: "{question}"
        
        {additional_context}
        
        Данные об ошибках:
        
        {formatted_errors}
        
        Сгенерируй подробный и информативный ответ на запрос пользователя, используя предоставленные данные об ошибках.
        Включи в ответ анализ ошибок, их причин и предпринятых мер, а также рекомендации по предотвращению подобных ошибок в будущем.
        """
        
        return {
            'system': system_prompt,
            'user': user_prompt
        }
        
        
    @staticmethod
    def build_process_classification_prompt(question: str, process_names: List[str]) -> Dict[str, str]:
        """
        Строит системный и пользовательский промпты для классификации запроса по бизнес-процессам.
        
        :param question: Вопрос пользователя
        :param process_names: Список названий процессов
        :return: Словарь с ключами 'system' и 'user' для промптов
        """
        # Системный промпт
        system_prompt = f"""Ты эксперт по классификации запросов о бизнес-процессах.
        
        Твоя задача: определить, к какому бизнес-процессу из предоставленного списка наиболее релевантен запрос пользователя.
        
        Список возможных бизнес-процессов:
        {', '.join(process_names)}
        
        Проанализируй запрос и выполни следующие действия:
        1. Проведи краткое рассуждение о том, к каким бизнес-процессам может относиться запрос
        2. Определи топ-3 наиболее релевантных бизнес-процесса и дай им оценки от 0 до 1
        
        Важно: выбирай только из предоставленного списка бизнес-процессов, не добавляй свои варианты.
        """
        
        # Пользовательский промпт
        example_process = process_names[0] if process_names else "Обработка заказа"
        
        user_prompt = f"""
        Запрос пользователя о бизнес-процессах: "{question}"
        
        Определи, к какому бизнес-процессу из списка наиболее релевантен этот запрос.
        
        Верни ответ в структурированном формате. Например:
        
        ```json
        {{
            "reasoning": "Запрос касается работы с клиентами и обработки их заказов",
            "top_processes": {{
                "{example_process}": 0.9,
                "{process_names[1] if len(process_names) > 1 else 'Обслуживание клиентов'}": 0.6,
                "{process_names[2] if len(process_names) > 2 else 'Управление складом'}": 0.3
            }}
        }}
        ```
        """
        
        return {
            'system': system_prompt,
            'user': user_prompt
        }

    @staticmethod
    def build_process_answer_prompt(question: str, processes: List[Dict[str, Any]], additional_context: str = "") -> Dict[str, str]:
        """
        Строит системный и пользовательский промпты для генерации ответа о бизнес-процессах.
        
        :param question: Вопрос пользователя
        :param processes: Список бизнес-процессов
        :param additional_context: Дополнительный контекст
        :return: Словарь с ключами 'system' и 'user' для промптов
        """
        # Системный промпт
        system_prompt = """Ты эксперт по бизнес-процессам и BPMN.
        
        Твоя задача: дать информативный ответ на запрос пользователя о бизнес-процессах на основе предоставленных данных.
        
        Ответ должен быть:
        1. Структурированным и информативным
        2. Содержать ключевую информацию о бизнес-процессах
        3. Отформатирован в виде Markdown
        4. Включать пояснения и рекомендации при необходимости
        
        Не включай в ответ информацию, которой нет в предоставленных данных.
        """
        
        # Форматируем данные о процессах для промпта
        formatted_processes = ""
        for i, process in enumerate(processes, 1):
            formatted_processes += f"### Процесс {i}:\n"
            formatted_processes += f"**ID**: {process.get('id', '')}\n"
            formatted_processes += f"**Название**: {process.get('name', '')}\n"
            
            if process.get('description'):
                formatted_processes += f"**Описание**: {process.get('description')}\n"
                
            if process.get('text_description'):
                formatted_processes += f"**Текстовое описание**: {process.get('text_description')}\n"
            
            formatted_processes += "\n---\n\n"
        
        # Пользовательский промпт
        user_prompt = f"""
        Запрос пользователя: "{question}"
        
        {additional_context}
        
        Данные о бизнес-процессах:
        
        {formatted_processes}
        
        Сгенерируй подробный и информативный ответ на запрос пользователя, используя предоставленные данные о бизнес-процессах.
        Включи в ответ анализ процессов и их описания, а также рекомендации по улучшению при необходимости.
        """
        
        return {
            'system': system_prompt,
            'user': user_prompt
        }