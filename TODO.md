# ToDo и План развития архитектуры инструментов

Этот документ описывает следующие шаги по улучшению архитектуры и содержит инструкции по работе с текущей реализацией.

## Часть 1: Инструкция по добавлению новых инструментов (Текущая архитектура)

Чтобы добавить новый инструмент в систему, нужно выполнить 2 простых шага.

**Пример:** Создание инструмента `FilterByPriorityTool` для поиска рисков с приоритетом выше заданного значения.

---

### **Шаг 1: Создание файла с классом нового инструмента**

1.  **Создайте новый файл** в директории `app/tools/`. Например, `app/tools/priority_filter_tool.py`.

2.  **Определите в нем класс**, который наследуется от `BaseTool` и реализует два обязательных метода: `get_schema()` и `execute()`.

    ```python
    # app/tools/priority_filter_tool.py

    import pandas as pd
    from typing import Dict, Any, Tuple
    from app.tools.base_tool import BaseTool
    from app.utils.logging import setup_logger

    logger = setup_logger(__name__)

    class FilterByPriorityTool(BaseTool):
        """
        Инструмент для фильтрации рисков по числовому значению приоритета.
        """

        def get_schema(self) -> Dict[str, Any]:
            """
            Определяет схему для LLM. Описывает, как вызывать этот инструмент.
            """
            return {
                "type": "function",
                "function": {
                    "name": "filter_by_priority",
                    "description": "Фильтрует записи по числовому полю, находя те, что выше или равны заданному порогу.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "priority_threshold": {
                                "type": "number",
                                "description": "Минимальный порог приоритета (например, 0.7)."
                            },
                            "column_to_check": {
                                "type": "string",
                                "description": "Название колонки для проверки приоритета (например, 'risk_priority')."
                            }
                        },
                        "required": ["priority_threshold", "column_to_check"]
                    }
                }
            }

        def execute(self, df: pd.DataFrame, priority_threshold: float, column_to_check: str, **kwargs) -> Tuple[pd.DataFrame, Dict[int, float]]:
            """
            Выполняет логику фильтрации по приоритету.
            """
            if df.empty or column_to_check not in df.columns:
                logger.warning(f"FilterByPriorityTool: DataFrame пуст или колонка '{column_to_check}' не найдена.")
                return pd.DataFrame(), {}

            numeric_column = pd.to_numeric(df[column_to_check], errors='coerce')
            result_df = df[numeric_column >= priority_threshold].copy()

            result_df['relevance_score'] = pd.to_numeric(result_df[column_to_check], errors='coerce')
            scores = pd.Series(result_df.relevance_score, index=result_df.index).to_dict()

            logger.info(f"FilterByPriorityTool: Найдено {len(result_df)} записей с приоритетом >= {priority_threshold}.")

            return result_df, scores
    ```

---

### **Шаг 2: Регистрация нового инструмента**

1.  **Откройте файл:** `app/tools/registry.py`

2.  **Добавьте две строки:** импортируйте новый класс и зарегистрируйте его экземпляр в методе `_register_tools`.

    ```python
    # app/tools/registry.py

    from app.tools.keyword_search_tool import KeywordSearchTool
    from app.tools.priority_filter_tool import FilterByPriorityTool  # <-- 1. ДОБАВИТЬ ИМПОРТ

    # ...

    class ToolRegistry:
        # ...
        def _register_tools(self):
            # ...
            keyword_search = KeywordSearchTool()
            self.register_tool(keyword_search)
            
            # <-- 2. ДОБАВИТЬ РЕГИСТРАЦИЮ
            priority_filter = FilterByPriorityTool()
            self.register_tool(priority_filter)
    ```

После этих двух шагов `ToolExecutor` автоматически сможет предлагать новый инструмент LLM для всех пайплайнов, где он вызывается.

---

## Часть 2: План по внедрению контекстно-зависимых инструментов

Текущая архитектура предлагает LLM *все* зарегистрированные инструменты для *любого* запроса. Следующим шагом является внедрение маппинга, чтобы предлагать только релевантный набор инструментов для каждого конкретного пайплайна (типа данных).

### Вариант 1: Маппинг на уровне Пайплайна (Рекомендуемый)

**Идея:** Каждый класс пайплайна сам объявляет, какие инструменты он поддерживает. Это делает архитектуру явной и объектно-ориентированной.

**План реализации:**

1.  **Модифицировать `BasePipeline`:**
    -   Добавить новый абстрактный метод:
        ```python
        @abstractmethod
        def get_tool_names(self) -> List[str]:
            """Возвращает список имен инструментов, релевантных для этого пайплайна."""
            pass
        ```

2.  **Реализовать метод в дочерних пайплайнах:**
    -   В `RisksPipeline`:
        ```python
        def get_tool_names(self) -> List[str]:
            return ["search_by_keywords", "filter_by_priority"]
        ```
    -   В `ContractorsPipeline` (в будущем):
        ```python
        def get_tool_names(self) -> List[str]:
            return ["search_by_keywords"]
        ```

3.  **Модифицировать `ToolRegistry`:**
    -   Добавить новый метод для получения схем по списку имен:
        ```python
        def get_schemas_by_names(self, names: List[str]) -> List[Dict[str, Any]]:
            """Возвращает схемы только для инструментов с указанными именами."""
            all_schemas = self.get_all_schemas()
            return [schema for schema in all_schemas if schema.get("function", {}).get("name") in names]
        ```

4.  **Модифицировать `ToolExecutor`:**
    -   Изменить сигнатуру метода `select_and_execute`, чтобы он принимал список доступных инструментов.
        ```python
        def select_and_execute(self, question: str, df: pd.DataFrame, available_tool_names: List[str], **kwargs):
            # ...
            relevant_schemas = self.registry.get_schemas_by_names(available_tool_names)
            # ...
            self.llm_client.chat_completion_with_tools(..., tools=relevant_schemas, ...)
        ```

5.  **Обновить вызов в пайплайнах:**
    -   В методе `_filter_data` пайплайна вызов будет выглядеть так:
        ```python
        self.tool_executor.select_and_execute(
            # ...
            available_tool_names=self.get_tool_names() 
        )
        ```

### Вариант 2: Централизованный Маппинг (Конфигурационный)

**Идея:** Создать единый словарь или конфигурационный файл, который определяет, какие инструменты доступны для каждого типа кнопки.

**План реализации:**

1.  **Создать файл с маппингом:**
    -   Например, `app/tools/mapping.py`:
        ```python
        from app.domain.enums import ButtonType

        TOOL_MAPPING = {
            ButtonType.RISKS: ["search_by_keywords", "filter_by_priority"],
            ButtonType.CONTRACTORS: ["search_by_keywords"],
            ButtonType.ERRORS: [],
            ButtonType.PROCESSES: []
        }
        ```

2.  **Модифицировать `ToolExecutor`:**
    -   Изменить сигнатуру `select_and_execute`, чтобы он принимал `button_type`.
        ```python
        from app.tools.mapping import TOOL_MAPPING
        from app.domain.enums import ButtonType

        def select_and_execute(self, question: str, df: pd.DataFrame, button_type: ButtonType, **kwargs):
            available_tool_names = TOOL_MAPPING.get(button_type, [])
            # ... дальше логика получения схем и вызова LLM, как в Варианте 1
        ```

3.  **Обновить вызов в пайплайнах:**
    -   Пайплайн при вызове `ToolExecutor` должен будет передавать свой `button_type`.
        ```python
        self.tool_executor.select_and_execute(
            # ...
            button_type=self.button_type 
        )
        ```
