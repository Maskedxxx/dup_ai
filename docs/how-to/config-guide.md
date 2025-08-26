# Управление конфигурацией DUP AI

## Как менять настройки в config.py

### app_settings - изменения влияют на:
```python
# В config.py меняете:
app_settings.debug = True

# Влияет на:
- app/main.py → FastAPI debug режим
- app/utils/logging.py → включение DEBUG логов и детальных промптов (3 места)
- app/utils/prompt_builder.py → формат промптов для LLM

# app_settings.host/port → app/main.py (uvicorn сервер)
# app_settings.app_name → app/main.py (название FastAPI, метаданные)
```

### llm_settings - изменения влияют на:
```python
# В config.py меняете:
llm_settings.ollama_model = "llama3.2:3b"

# Влияет на:
- app/adapters/llm_client.py → подключение к LLM (base_url, api_key, model_name)
```

### Доменные настройки (contractor/risk/error/process_settings):
```python
# В config.py меняете:
risk_settings.max_results = 50

# Влияет на:
- app/api/v1/endpoints.py → лимиты результатов API (если limit не указан в запросе)
- app/adapters/excel_loader.py → пути к файлам данных
- app/pipelines/base.py → пути к файлам для логирования
```

## Специализированные конфигурации

### ClassificationConfig - переопределяется в классах сервисов:
```python
# В config.py меняете:
RISK = {
    "column_name": "risk_category",  # было project_name
    "item_type": "категория"         # было проект
}

# Влияет на:
- app/services/base_classifier.py → get_column_name(), get_item_type()
- Все *_classifier.py сервисы → из какой колонки брать элементы для классификации
- Промпты для LLM → как называть тип элементов в промптах
```

**Текущая структура:**
- `CONTRACTOR`: column_name="work_types" → классифицирует по видам работ
- `RISK`: column_name="project_name" → классифицирует по проектам  
- `ERROR`: column_name="project" → классифицирует по проектам
- `PROCESS`: column_name="name" → классифицирует по именам процессов

### SmartFilteringSettings - переопределяется в ToolExecutor:
```python
# В config.py меняете:
strategy: Dict[str, str] = {
    "contractors": "keybert",  # было "none" 
    "risks": "llm",           # было "keybert"
    "errors": "both"          # было "none"
}

strategy_tool_map: Dict[str, str] = {
    "keybert": "new_keyword_tool",    # было "search_by_keywords"
    "llm": "smart_filter_tool"        # новый маппинг
}

# Влияет на:
- app/tools/tool_executor.py → apply_smart_filtering() выбор стратегии по типу пайплайна
- app/tools/tool_executor.py → _execute_keybert_strategy() выбор инструмента
```

## Переопределения значений по коду

### Значения из .env переопределяются в местах использования:

**1. Лимиты API в endpoints.py:**
```python
# Если в запросе limit=None, берется из настроек:
limits = {
    ButtonType.CONTRACTORS: contractor_settings.max_results,  # по умолчанию 20
    ButtonType.RISKS: risk_settings.max_results,              # по умолчанию 20
    ButtonType.ERRORS: error_settings.max_results,            # по умолчанию 20
    ButtonType.PROCESSES: process_settings.max_results        # по умолчанию 20
}
# Но если в URL ?limit=100, то используется 100
```

**2. Пути к файлам в excel_loader.py:**
```python
# Создается маппинг из настроек:
file_paths = {
    ButtonType.CONTRACTORS: (contractor_settings.data_file_path, "файл подрядчиков"),
    ButtonType.RISKS: (risk_settings.data_file_path, "файл рисков"),
    # ...
}
# При загрузке используется соответствующий путь
```

**3. Режим логирования в logging.py:**
```python
# DEBUG флаг влияет на детальность логов:
log_mode = "DEBUG" if app_settings.debug else "PROD"

# В нескольких методах проверяется:
if app_settings.debug:
    # детальные логи промптов и ответов LLM
if not app_settings.debug:
    return  # пропуск детальных логов
```

## Прямые изменения в config.py (без .env)

```python
# Можно напрямую переопределить после создания экземпляра:
app_settings.debug = True
risk_settings.max_results = 100

# Или изменить значения по умолчанию в классах:
class RiskSettings(BaseAppSettings):
    max_results: int = 50  # было 20

# Или изменить специализированные настройки:
classification_config.RISK["column_name"] = "new_column"
smart_filtering_settings.strategy["contractors"] = "keybert"
```