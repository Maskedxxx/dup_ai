# Как добавлять инструменты (tools) и встраивать в пайплайны

Этот документ — практичный гайд: как написать новый tool (инструмент фильтрации), зарегистрировать его и включить только в нужные пайплайны на шаге «Умной фильтрации» (6.5).

## Что такое инструмент
- Мини-функция фильтрации/ранжирования данных, реализующая контракт `BaseTool`.
- Принимает `DataFrame` (+ свои параметры) и возвращает кортеж `(filtered_df, scores_by_index)`.
- Используется внутри `ToolExecutor` на шаге 6.5 (`BasePipeline`).

## Где инструмент живёт и кто его вызывает
- Код инструмента: `app/tools/implementations/...` (общие — в `_shared/`).
- Реестр инструментов: `app/tools/registry.py` — единая точка регистрации/доступа.
- Оркестратор: `app/tools/tool_executor.py` — выбирает стратегию и вызывает инструмент.
- Конфигурация стратегий: `app/config.py::SmartFilteringSettings`.

## Быстрый чеклист
- Есть класс-наследник `BaseTool` с методами `get_schema()` и `execute()`.
- Инструмент зарегистрирован в `ToolRegistry._register_tools()`.
- В `SmartFilteringSettings.strategy` выставлена стратегия для нужного пайплайна.
- В `SmartFilteringSettings.strategy_tool_map` указан `tool_name` → имя инструмента.
- При новой стратегии добавлена ветка в `ToolExecutor.apply_smart_filtering()`.

## Шаг 1. Создайте класс инструмента
Рекомедуемое расположение: `app/tools/implementations/<domain>/your_tool.py` или `_shared/` для общего инструмента.

Минимальный шаблон:

```python
import pandas as pd
from typing import Dict, Any, Tuple
from app.tools.base_tool import BaseTool
from app.utils.logging import setup_logger

logger = setup_logger(__name__)

class FilterByColumnTool(BaseTool):
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "filter_by_column",  # Уникальное имя инструмента
                "description": "Фильтрует строки по вхождению подстроки в указанной колонке.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "column": {"type": "string", "description": "Имя колонки для поиска"},
                        "query": {"type": "string", "description": "Подстрока для поиска"},
                        "top_n": {"type": "integer", "default": 5}
                    },
                    "required": ["column", "query"],
                    "additionalProperties": False
                },
                "strict": True
            }
        }

    def execute(self, df: pd.DataFrame, column: str, query: str, top_n: int = 5, **kwargs) -> Tuple[pd.DataFrame, Dict[int, float]]:
        if df.empty or column not in df.columns or not query:
            logger.warning("Пустые входные данные для FilterByColumnTool.")
            return df.head(top_n), {}

        matched = df[df[column].astype(str).str.contains(query, case=False, na=False)]
        if matched.empty:
            return df.head(top_n), {}

        # Простейший скоринг: 1.0 для совпавших
        scores = {idx: 1.0 for idx in matched.index}
        result = matched.head(top_n)
        # Возвращаем строки по исходным индексам (важно для маппинга скорингов)
        return df.loc[result.index], scores
```

Примечания:
- Контракт определён в `app/tools/base_tool.py::BaseTool`.
- Если нужен базовый скоринг по ключевым словам, можно использовать `calculate_relevance_score()` из того же файла.

## Шаг 2. Зарегистрируйте инструмент в реестре
Откройте `app/tools/registry.py`, импортируйте класс и добавьте его в `_register_tools()`:

```python
from app.tools.implementations._shared.keyword_search_tool import KeywordSearchTool
from app.tools.implementations.<domain>.your_tool import FilterByColumnTool  # новый импорт

def _register_tools(self):
    keyword_search = KeywordSearchTool()
    self.register_tool(keyword_search)

    filter_by_column = FilterByColumnTool()          # новый инструмент
    self.register_tool(filter_by_column)             # регистрация
```

Проверка: метод `ToolRegistry.get_available_tool_names()` вернёт список имен — ваше имя должно совпасть с `get_schema()["function"]["name"]`.

## Шаг 3. Привяжите инструмент к стратегии
Конфигурация: `app/config.py::SmartFilteringSettings`.

Вариант A — переиспользовать готовую стратегию (например, `keybert`) и заменить инструмент:

```python
strategy = {
    "contractors": "none",
    "risks": "keybert",     # умная фильтрация включена
    "errors": "none",
    "processes": "none",
}

strategy_tool_map = {
    "keybert": "filter_by_column",  # вместо "search_by_keywords"
}
```

Важно: стратегия `keybert` сама генерирует `keywords` через `KeyBERTService`. Если вашему инструменту нужны другие параметры, предпочтительнее создать отдельную стратегию.

Вариант B — добавить новую стратегию:
1) Укажите стратегию для нужного пайплайна в `strategy` (например, `"risks": "mytool"`).
2) В `strategy_tool_map` добавьте соответствие: `"mytool": "filter_by_column"`.
3) В `app/tools/tool_executor.py` добавьте ветку и реализацию:

```python
class ToolExecutor:
    def apply_smart_filtering(...):
        ...
        elif strategy == "mytool":
            return self._execute_mytool_strategy(question, df, button_type, **kwargs)
        ...

    def _execute_mytool_strategy(self, question, df, button_type, **kwargs):
        tool_name = smart_filtering_settings.strategy_tool_map.get("mytool")
        tool = self.registry.get_tool(tool_name)
        if not tool:
            logger.error(f"Инструмент '{tool_name}' не найден")
            return df, {}

        # Сформируйте аргументы под ваш инструмент
        args = {
            "df": df,
            # добавьте нужные параметры, например:
            # "column": kwargs.get("column"),
            # "query": kwargs.get("query"),
            "top_n": kwargs.get("top_n", 5),
        }
        return tool.execute(**args)
```

## Как это встраивается в пайплайн
- Основной вызов — `BasePipeline.process()` → шаг 6.5: `tool_executor.apply_smart_filtering(...)`.
- Если инструмент вернул непустой результат и `scores`, пайплайн использует их; иначе остаются данные шага 6.
- Где посмотреть: `app/pipelines/base.py` (поиск по строке «ШАГ 6.5: Умная фильтрация»).

## Отладка и типовые ошибки
- Список доступных инструментов: `tool_registry.get_available_tool_names()`.
- Логи `ToolExecutor` и инструмента помогут диагностировать параметры/ошибки.
- Важные проверки в инструментах:
  - Наличие нужных колонок в `df` (логируйте понятную ошибку).
  - Пустые входы (пустой `df`/параметры) — возвращайте исходные `top_n` и `{}`.
  - Сохраняйте исходные индексы строк: используйте `df.loc[result.index]`.

## Где посмотреть готовый пример
- Готовый инструмент: `app/tools/implementations/_shared/keyword_search_tool.py`.
- Его стратегия и вызов: `app/tools/tool_executor.py::_execute_keybert_strategy()`.
- Конфиг стратегий: `app/config.py::SmartFilteringSettings`.

