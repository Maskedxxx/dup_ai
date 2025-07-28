# Core Principles
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.
Communicate with the user in Russian, as it is my native language.

# Version Control
NEVER commit or push changes unless explicitly instructed to do so by the User.

# Workflows
The agent must operate in one of two modes, depending on the User's request.

## 1. Code Modification Workflow
This workflow is active when the User asks to make specific changes, improvements, fixes, or write new code.

1.  **Execute Task:** Fulfill the direct task given by the User (modify, create, delete code/files).
2.  **Summarize:** After completing the task, ALWAYS provide a concise summary of the work done. (e.g., "I have modified `main.py` to add the `calculate_price` function and updated `utils.py` to support new parameters.")
3.  **Suggest Improvements:** After the summary, if you identify clear opportunities for further code improvement (e.g., refactoring, optimization, potential bug fixes, readability enhancements), suggest them to the User.
4.  **Await Confirmation:** NEVER apply these additional improvements automatically. Clearly state your suggestions and explicitly ask the User for permission to proceed. (e.g., "During the process, I noticed the error handling in `api.js` could be made more robust. Would you like me to add `try-catch` blocks?")

## 2. Analysis & Brainstorming Workflow
This workflow is active when the User asks for analysis, brainstorming, a code review, or feedback.

1.  **No File Changes:** In this mode, NEVER modify, create, or delete any files in the project. Your task is analysis and text generation only.
2.  **Provide Report:** Your output must be a textual report, summary, or analysis as requested by the User.
3.  **Demonstrate with Code:** You CAN and SHOULD write code snippets inside your response to demonstrate ideas, suggest refactoring, or illustrate concepts. These examples must be part of your chat response, not changes to the project files.

---

# История работы с Claude Code

## 23 июня 2025 - Реализация единой конфигурации классификации

### Задача
Создать единый конфиг в котором можно указывать колонку для классификации LLM по сущностям для фильтрации данных.

### Что было сделано

#### 1. **Создана единая конфигурация классификации**
- **Файл**: `app/config.py` (строки 125-189)
- **Класс**: `ClassificationConfig` с настройками для всех типов сущностей
- **Структура**:
  ```python
  CONTRACTOR = {"column_name": "work_types", "item_type": "вид работ"}
  RISK = {"column_name": "project_name", "item_type": "проект"}  
  ERROR = {"column_name": "project_name", "item_type": "проект"}
  PROCESS = {"column_name": "process_name", "item_type": "процесс"}
  ```

#### 2. **Обновлен базовый классификатор**
- **Файл**: `app/services/base_classifier.py` (строки 20-74)
- **Изменения**:
  - Добавлен параметр `entity_type` в конструктор
  - Автоматическая загрузка конфигурации из `ClassificationConfig`
  - Fallback методы для совместимости с существующим кодом
  - Гибкое получение `column_name` и `item_type` из конфига

#### 3. **Обновлены все конкретные классификаторы**
- **Файлы**: `contractor_classifier.py`, `risk_classifier.py`, `error_classifier.py`, `process_classifier.py`
- **Изменения**:
  - Передача `entity_type` в базовый класс через `super().__init__()`
  - Автоматическое использование настроек из единого конфига
  - Сохранена обратная совместимость

#### 4. **Создан универсальный тестер пайплайнов**
- **Файл**: `test_universal_pipeline.py`
- **Возможности**:
  - Интерактивный режим: `python test_universal_pipeline.py`
  - CLI режим: `python test_universal_pipeline.py risks "вопрос" manufacturing`
  - Поддержка всех типов кнопок (contractors/risks/errors/processes)
  - Отображение конфигурации классификации в реальном времени
  - Детальные логи обработки каждого шага

#### 5. **Обновлена документация**
- **README.md**: 
  - Добавлен раздел "Единая конфигурация классификации" с примерами
  - Добавлен раздел "Тестирование" с описанием universal tester
  - Обновлен список архитектурных решений
- **architecture-cheatsheet.md**:
  - Добавлен раздел о `ClassificationConfig`
  - Описан принцип работы единой конфигурации

### Техническая реализация

**Принцип работы нового конфига:**
1. LLM классификация загружает уникальные значения из указанной `column_name`
2. Создаются динамические Pydantic модели с Literal типами
3. Данные фильтруются по выбранному LLM элементу из `column_name`
4. LLM генерирует ответ используя `item_type` в промптах

**Как изменить конфигурацию:**
```python
# Изменить колонку для рисков
ClassificationConfig.RISK["column_name"] = "risk_category"
ClassificationConfig.RISK["item_type"] = "категория риска"
```

### Git коммиты
- `feat: add unified classification configuration system` (d935d08)
- `feat: add universal pipeline test script` (dfa84c5)  
- `docs: update documentation for unified classification configuration` (5ad6b11)

### Результат
✅ **Гибкая конфигурация**: Можно легко менять колонки для классификации в едином месте  
✅ **Обратная совместимость**: Существующий код продолжает работать  
✅ **Универсальное тестирование**: Один скрипт для проверки всех пайплайнов  
✅ **Полная документация**: Описание настройки и использования системы
