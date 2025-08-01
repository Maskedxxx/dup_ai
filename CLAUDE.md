# <project_title>DUP AI - Семантический граф проекта для AI агентов</project_title>

## <navigation_graph>🧠 Навигационный граф проекта</navigation_graph>

<architecture_diagram>
```xml
<mermaid>
graph TB
    subgraph "📋 ДОКУМЕНТАЦИЯ"
        README[📄 README.md<br/>Архитектура + Быстрый старт]
        TECH[📄 tech_docs.md<br/>Операционная документация]
        ARCH[📄 architecture-cheatsheet.md<br/>Паттерны + Архитектурные решения]
        API_EX[📄 api_examples.md<br/>Примеры использования API]
        FLOW[📄 flow-diagram.mermaid<br/>Диаграмма workflow]
        CLAUDE[📄 CLAUDE.md<br/>Этот файл - навигатор для AI]
    end

    subgraph "⚙️ КОНФИГУРАЦИЯ"
        CONFIG[📁 app/config.py<br/>🔧 Настройки + DI контейнер + ClassificationConfig]
        ENV[📄 .env<br/>🌐 Переменные окружения]
        ENV_EX[📄 .env.example<br/>📋 Шаблон переменных]
        REQ[📄 requirements.txt<br/>📦 Зависимости Python]
    end

    subgraph "🌐 API СЛОЙ"
        MAIN[📁 app/main.py<br/>🚀 FastAPI приложение + точка входа]
        ENDPOINTS[📁 app/api/v1/endpoints.py<br/>🔌 REST endpoints]
        SCHEMAS[📁 app/api/v1/schemas.py<br/>📊 Pydantic модели запросов/ответов]
    end

    subgraph "🔄 ПАЙПЛАЙНЫ APPLICATION LAYER"
        BASE_PIPE[📁 app/pipelines/base.py<br/>🏗️ BasePipeline + 8-шаговый Template Method]
        CONT_PIPE[📁 app/pipelines/contractors_pipeline.py<br/>👷 Пайплайн подрядчиков]
        RISK_PIPE[📁 app/pipelines/risks_pipeline.py<br/>⚠️ Пайплайн рисков + ToolExecutor]
        ERR_PIPE[📁 app/pipelines/errors_pipeline.py<br/>❌ Пайплайн ошибок]
        PROC_PIPE[📁 app/pipelines/processes_pipeline.py<br/>⚡ Пайплайн процессов]
        PIPE_INIT[📁 app/pipelines/__init__.py<br/>🔗 Регистрация пайплайнов]
    end

    subgraph "🧩 СЕРВИСЫ BUSINESS LOGIC"
        subgraph "Нормализация"
            BASE_NORM[📁 app/services/base_normalization.py<br/>🧹 Базовый класс очистки данных]
            CONT_NORM[📁 app/services/contractor_normalization.py<br/>👷 Нормализация подрядчиков]
            RISK_NORM[📁 app/services/risk_normalization.py<br/>⚠️ Нормализация рисков]
            ERR_NORM[📁 app/services/error_normalization.py<br/>❌ Нормализация ошибок]
            PROC_NORM[📁 app/services/process_normalization.py<br/>⚡ Нормализация процессов]
        end

        subgraph "Классификация"
            BASE_CLASS[📁 app/services/base_classifier.py<br/>🎯 Базовый классификатор + динамические Literal типы]
            CONT_CLASS[📁 app/services/contractor_classifier.py<br/>👷 Классификация по видам работ]
            RISK_CLASS[📁 app/services/risk_classifier.py<br/>⚠️ Классификация по проектам]
            ERR_CLASS[📁 app/services/error_classifier.py<br/>❌ Классификация по проектам]
            PROC_CLASS[📁 app/services/process_classifier.py<br/>⚡ Классификация по процессам]
        end

        subgraph "Генерация ответов"
            BASE_ANS[📁 app/services/base_answer_generator.py<br/>💬 Базовый генератор ответов]
            CONT_ANS[📁 app/services/contractor_answer_generator.py<br/>👷 Ответы по подрядчикам]
            RISK_ANS[📁 app/services/risk_answer_generator.py<br/>⚠️ Ответы по рискам]
            ERR_ANS[📁 app/services/error_answer_generator.py<br/>❌ Ответы по ошибкам]
            PROC_ANS[📁 app/services/process_answer_generator.py<br/>⚡ Ответы по процессам]
        end

        KEYBERT[📁 app/services/keybert_service.py<br/>🔍 Семантический поиск по ключевым словам]
    end

    subgraph "🛠️ ИНСТРУМЕНТЫ TOOLS"
        BASE_TOOL[📁 app/tools/base_tool.py<br/>🔧 Абстрактный класс инструментов]
        REGISTRY[📁 app/tools/registry.py<br/>📚 Автоматическая регистрация инструментов]
        EXECUTOR[📁 app/tools/tool_executor.py<br/>⚡ Выполнитель инструментов + LLM интеграция]
        KEYWORD_TOOL[📁 app/tools/implementations/_shared/keyword_search_tool.py<br/>🔍 Поиск по ключевым словам + лемматизация]
    end

    subgraph "🏗️ ДОМЕН CORE"
        ENUMS[📁 app/domain/enums.py<br/>📝 ButtonType + RiskCategory]
        CONT_MODEL[📁 app/domain/models/contractor.py<br/>👷 Модель подрядчика]
        RISK_MODEL[📁 app/domain/models/risk.py<br/>⚠️ Модель риска]
        ERR_MODEL[📁 app/domain/models/error.py<br/>❌ Модель ошибки]
        PROC_MODEL[📁 app/domain/models/process.py<br/>⚡ Модель процесса]
        ANS_MODEL[📁 app/domain/models/answer.py<br/>💬 Модель ответа]
    end

    subgraph "🔌 АДАПТЕРЫ INFRASTRUCTURE"
        EXCEL[📁 app/adapters/excel_loader.py<br/>📊 Загрузка Excel файлов]
        LLM[📁 app/adapters/llm_client.py<br/>🤖 Клиент для Ollama LLM]
    end

    subgraph "🛠️ УТИЛИТЫ"
        LOGGING[📁 app/utils/logging.py<br/>📝 Блочная система логирования + Pipeline ID]
        PROMPT[📁 app/utils/prompt_builder.py<br/>🎭 Построитель промптов для LLM]
    end

    subgraph "📊 ДАННЫЕ"
        CONT_DATA[📄 data/contractors.xlsx<br/>👷 База подрядчиков]
        RISK_DATA[📄 data/riski.xlsx<br/>⚠️ База рисков проектов]
        ERR_DATA[📄 data/errors.xlsx<br/>❌ База ошибок проектов]
        PROC_DATA[📄 data/bpmn_processes.xlsx<br/>⚡ База бизнес-процессов]
    end

    subgraph "🧪 ТЕСТИРОВАНИЕ"
        UNIVERSAL_TEST[📄 test_universal_pipeline.py<br/>🔬 Универсальный тестер всех пайплайнов]
    end

    %% Связи между компонентами
    README --> ARCH
    README --> API_EX
    README --> FLOW
    ARCH --> BASE_PIPE

    MAIN --> ENDPOINTS
    ENDPOINTS --> SCHEMAS
    ENDPOINTS --> PIPE_INIT

    CONFIG --> BASE_PIPE
    CONFIG --> BASE_CLASS
    CONFIG --> EXECUTOR

    BASE_PIPE --> CONT_PIPE
    BASE_PIPE --> RISK_PIPE
    BASE_PIPE --> ERR_PIPE
    BASE_PIPE --> PROC_PIPE

    CONT_PIPE --> CONT_NORM
    CONT_PIPE --> CONT_CLASS
    CONT_PIPE --> CONT_ANS

    RISK_PIPE --> RISK_NORM
    RISK_PIPE --> RISK_CLASS
    RISK_PIPE --> RISK_ANS
    RISK_PIPE --> EXECUTOR

    EXECUTOR --> REGISTRY
    EXECUTOR --> KEYWORD_TOOL

    BASE_CLASS --> CONT_CLASS
    BASE_CLASS --> RISK_CLASS
    BASE_CLASS --> ERR_CLASS
    BASE_CLASS --> PROC_CLASS

    LLM --> BASE_CLASS
    LLM --> BASE_ANS
    LLM --> EXECUTOR

    EXCEL --> BASE_PIPE
    LOGGING --> BASE_PIPE
</mermaid>
```
</architecture_diagram>

## <knowledge_map>📚 Семантическая карта знаний для AI агентов</knowledge_map>

### <architecture_understanding>🎯 Если нужно понять АРХИТЕКТУРУ системы:</architecture_understanding>
- <file_reference>**`README.md`**</file_reference> → Общий обзор + чистая архитектура + 8-шаговый workflow + блочное логирование
- <file_reference>**`architecture-cheatsheet.md`**</file_reference> → Детальные паттерны + Template Method + Dynamic Literal Types + DI Container
- <file_reference>**`flow-diagram.mermaid`**</file_reference> → Визуальный workflow: Data Processing → Classification → Smart Filtering → Answer Generation

### <configuration_understanding>🔧 Если нужно понять КОНФИГУРАЦИЮ:</configuration_understanding>
- <file_reference>**`app/config.py`**</file_reference> →
  - <config_section>`ClassificationConfig`</config_section>: единая конфигурация классификации (column_name, item_type, description)
  - <config_section>`SmartFilteringSettings`</config_section>: стратегии фильтрации (none для большинства, keybert для рисков)
  - <config_section>`Container`</config_section>: DI контейнер для управления зависимостями
  - Настройки для всех сущностей: App, LLM, Contractor, Risk, Error, Process
- <file_reference>**`.env.example`**</file_reference> → Шаблон всех переменных окружения с префиксами

### <api_understanding>🌐 Если нужно понять API:</api_understanding>
- <file_reference>**`app/api/v1/endpoints.py`**</file_reference> → REST endpoints (/v1/ask, /v1/health) + обработка limit параметра
- <file_reference>**`app/api/v1/schemas.py`**</file_reference> → Pydantic модели (AskRequest, AskResponse) + валидация
- <file_reference>**`api_examples.md`**</file_reference> → Готовые cURL и Python примеры для всех типов запросов

### <pipelines_understanding>🔄 Если нужно понять ПАЙПЛАЙНЫ:</pipelines_understanding>
- <file_reference>**`app/pipelines/base.py`**</file_reference> → 
  - <pattern>Template Method Pattern</pattern> с 8 фиксированными шагами
  - <logging_system>Блочное логирование</logging_system> с уникальными Pipeline ID
  - Абстрактные методы для переопределения в наследниках
- <file_reference>**`app/pipelines/risks_pipeline.py`**</file_reference> → Единственный пайплайн с ToolExecutor интеграцией
- <pipeline_group>**Остальные пайплайны**</pipeline_group> → Стандартная логика без инструментов

### <services_understanding>🧩 Если нужно понять СЕРВИСЫ:</services_understanding>
- <service_category>**Нормализация**</service_category> (`app/services/*_normalization.py`):
  - <base_service>`BaseNormalizationService`</base_service> → Общая логика очистки DataFrame
  - <specialized_services>Специализированные классы</specialized_services> → Переименование колонок + валидация данных

- <service_category>**Классификация**</service_category> (`app/services/*_classifier.py`):
  - <base_service>`BaseClassifierService`</base_service> → Динамические Literal типы + единая конфигурация
  - Использует <config_reference>`ClassificationConfig`</config_reference> для определения column_name и item_type
  - LLM выбирает из точного списка без опечаток

- <service_category>**Генерация ответов**</service_category> (`app/services/*_answer_generator.py`):
  - <base_service>`BaseAnswerGeneratorService`</base_service> → Общая логика работы с LLM
  - <specialized_prompts>Специализированные промпты</specialized_prompts> для каждого типа данных

### <tools_understanding>🛠️ Если нужно понять ИНСТРУМЕНТЫ:</tools_understanding>
- <file_reference>**`app/tools/base_tool.py`**</file_reference> → Абстрактный класс: get_schema() + execute()
- <file_reference>**`app/tools/registry.py`**</file_reference> → Автоматическое сканирование и регистрация всех наследников BaseTool
- <file_reference>**`app/tools/tool_executor.py`**</file_reference> → 
  - Получает схемы всех инструментов от Registry
  - Отправляет в LLM для выбора подходящего инструмента
  - Выполняет выбранный инструмент с аргументами от LLM
- <file_reference>**`keyword_search_tool.py`**</file_reference> → Семантический поиск + pymorphy3 лемматизация

### <models_understanding>🏗️ Если нужно понять МОДЕЛИ:</models_understanding>
- <file_reference>**`app/domain/enums.py`**</file_reference> → ButtonType (contractors/risks/errors/processes) + RiskCategory
- <file_reference>**`app/domain/models/*.py`**</file_reference> → Pydantic модели для каждой сущности с валидацией
- <file_reference>**`app/domain/models/answer.py`**</file_reference> → Универсальная модель ответа системы

### <integrations_understanding>🔌 Если нужно понять ИНТЕГРАЦИИ:</integrations_understanding>
- <file_reference>**`app/adapters/excel_loader.py`**</file_reference> → Загрузка и парсинг Excel файлов
- <file_reference>**`app/adapters/llm_client.py`**</file_reference> → 
  - Клиент для Ollama API
  - Обработка JSON responses от LLM
  - Retry логика и error handling

### <utilities_understanding>🛠️ Если нужно понять УТИЛИТЫ:</utilities_understanding>
- <file_reference>**`app/utils/logging.py`**</file_reference> → 
  - <logging_function>`get_pipeline_logger()`</logging_function> → Создание логгера с Pipeline ID
  - <logging_system>Блочная система</logging_system>: start_pipeline_block() → log_step_ok() → end_pipeline_block()
  - DEBUG/PROD режимы логирования
- <file_reference>**`app/utils/prompt_builder.py`**</file_reference> → Построение промптов для разных задач LLM

### <data_understanding>📊 Если нужно понять ДАННЫЕ:</data_understanding>
- <file_reference>**`data/*.xlsx`**</file_reference> → Excel файлы с данными о подрядчиках, рисках, ошибках, процессах
- Структура определяется нормализационными сервисами

### <testing_understanding>🧪 Если нужно ТЕСТИРОВАТЬ:</testing_understanding>
- <file_reference>**`test_universal_pipeline.py`**</file_reference> → 
  - Интерактивный и CLI режимы тестирования
  - Поддержка всех типов кнопок и категорий рисков
  - Детальный вывод всех 8 шагов пайплайна

## <key_dependencies>🔗 Ключевые зависимости и связи</key_dependencies>

### <request_flow>Поток выполнения запроса:</request_flow>
1. <flow_step>**Client**</flow_step> → `endpoints.py` → выбор Pipeline по ButtonType
2. <flow_step>**Pipeline**</flow_step> → последовательное выполнение 8 шагов через Template Method
3. <flow_step>**Шаг 5 (Классификация)**</flow_step> → `BaseClassifierService` → `ClassificationConfig` → LLM
4. <flow_step>**Шаг 6 (Фильтрация)**</flow_step> → для рисков: `ToolExecutor` → `ToolRegistry` → LLM → `KeywordSearchTool`
5. <flow_step>**Шаг 8 (Генерация)**</flow_step> → `BaseAnswerGeneratorService` → LLM → финальный ответ

### <configuration_connections>Конфигурационные связи:</configuration_connections>
- <config_reference>`ClassificationConfig`</config_reference> → используется всеми классификаторами для единообразия
- <config_reference>`SmartFilteringSettings`</config_reference> → определяет, какие пайплайны используют инструменты
- <config_reference>`Container`</config_reference> (DI) → управляет жизненным циклом всех сервисов

### <architectural_patterns>Архитектурные паттерны:</architectural_patterns>
- <pattern>**Template Method**</pattern> → BasePipeline с 8 фиксированными шагами
- <pattern>**Factory**</pattern> → создание пайплайнов по ButtonType
- <pattern>**Strategy**</pattern> → разные стратегии фильтрации (none/keybert)
- <pattern>**Registry**</pattern> → автоматическая регистрация инструментов
- <pattern>**Dependency Injection**</pattern> → Container для управления зависимостями

## <ai_agent_hints>💡 Подсказки для AI агентов</ai_agent_hints>

### <modification_guidelines>Когда модифицировать код:</modification_guidelines>
1. <task>**Добавление нового типа данных**</task> → следуй паттерну: Model + Enum + 3 сервиса + Pipeline
2. <task>**Изменение логики классификации**</task> → редактируй `ClassificationConfig`, не код классификаторов
3. <task>**Добавление нового инструмента**</task> → наследуй `BaseTool`, Registry подхватит автоматически
4. <task>**Изменение стратегии фильтрации**</task> → редактируй `SmartFilteringSettings.strategy`

### <common_tasks>Частые задачи:</common_tasks>
- <task>**Отладка**</task> → включи `DEBUG=true` → анализируй `LOGS/dup_ai.log` по Pipeline ID
- <task>**Тестирование**</task> → используй `test_universal_pipeline.py` с разными параметрами
- <task>**API интеграция**</task> → используй примеры из `api_examples.md`

### <critical_principles>Критически важные принципы:</critical_principles>
- <principle>**8 шагов пайплайна**</principle> → неизменны, Template Method в BasePipeline
- <principle>**Единая классификация**</principle> → через ClassificationConfig, не хардкод
- <principle>**Блочное логирование**</principle> → каждый запрос имеет уникальный Pipeline ID
- <principle>**Условная логика инструментов**</principle> → только риски используют ToolExecutor

## <entry_points>🎯 Точки входа для разных задач</entry_points>

### <code_research>🔍 ИССЛЕДОВАНИЕ КОДА:</code_research>
- Начни с <file_reference>**`CLAUDE.md`**</file_reference> (этот файл) → получи общую карту
- Затем <file_reference>**`README.md`**</file_reference> → пойми архитектуру
- Затем <file_reference>**`architecture-cheatsheet.md`**</file_reference> → изучи паттерны
- Затем конкретные файлы из графа выше

### <debugging>🐛 ОТЛАДКА ПРОБЛЕМ:</debugging>
1. <debug_step>**`LOGS/dup_ai.log`**</debug_step> → найди Pipeline ID проблемного запроса
2. <debug_step>**`app/pipelines/base.py`**</debug_step> → пойми на каком шаге падает
3. <debug_step>**`app/config.py`**</debug_step> → проверь конфигурацию
4. <debug_step>**`test_universal_pipeline.py`**</debug_step> → воспроизведи проблему

### <feature_development>🔧 РАЗРАБОТКА НОВЫХ ФИЧЕЙ:</feature_development>
1. <dev_step>**`app/domain/enums.py`**</dev_step> → добавь новые типы
2. <dev_step>**`app/domain/models/`**</dev_step> → создай модели
3. <dev_step>**`app/services/`**</dev_step> → реализуй бизнес-логику
4. <dev_step>**`app/pipelines/`**</dev_step> → создай пайплайн
5. <dev_step>**`app/api/v1/`**</dev_step> → обнови API

### <data_analysis>📊 АНАЛИЗ ДАННЫХ:</data_analysis>
- <analysis_step>**`data/*.xlsx`**</analysis_step> → изучи структуру данных
- <analysis_step>**`app/adapters/excel_loader.py`**</analysis_step> → пойми как загружаются данные
- <analysis_step>**`app/services/*_normalization.py`**</analysis_step> → как обрабатываются данные

### <llm_work>🤖 РАБОТА С LLM:</llm_work>
- <llm_step>**`app/adapters/llm_client.py`**</llm_step> → интеграция с Ollama
- <llm_step>**`app/utils/prompt_builder.py`**</llm_step> → конструирование промптов
- <llm_step>**`app/services/*_classifier.py`**</llm_step> → логика классификации
- <llm_step>**`app/services/*_answer_generator.py`**</llm_step> → генерация ответов