# Шаг 4: Загрузка элементов для классификации (внутри контура пайплайна)

## Вход
- DataFrame: предобработанный набор записей (Шаг 3).
- Сервис классификации: доменный (`Contractor/Risk/Error/ProcessClassifierService`).

## Что происходит внутри
1) Определяется колонка-источник
- Решается методом `BaseClassifierService.get_column_name()`:
  - Если в конструктор доменного сервиса передан `entity_type`, берётся `column_name` из `ClassificationConfig` (`app/config.py`).
  - Иначе используется доменный fallback-метод `_get_column_name_fallback()` (реализован в `*ClassifierService`).
  - Примеры fallback: contractors → `work_types`, risks/errors → `project_name`, processes → `process_name`.

2) Извлекаются уникальные элементы
- Берём непустые уникальные значения из выбранной колонки и сохраняем их в `classifier_service.items_list`.
- Где: `BaseClassifierService.load_items(df)`.

Под капотом `load_items`:
- Проверяет наличие колонки; если нет — предупреждение и `[]`.
- `df[column].dropna().unique().tolist()` → фильтр пустых и нестроковых значений.
- Сохраняет список в `self.items_list` для шага классификации.

3) Совместимость по доменам (алиасы методов)
- В пайплайнах используются «говорящие» методы, которые под капотом вызывают `load_items`:
  - Contractors: `load_work_types(df)`
  - Risks: `load_project_names(df)`
  - Errors: `load_project_names(df)`
  - Processes: `load_process_names(df)`

Где вызывается:
- `BasePipeline.process()` вызывает `self._load_classifier_items(processed_df)` (шаг 4).
- В доменных пайплайнах метод `_load_classifier_items` переопределён и делегирует в алиасы:
  - `app/pipelines/contractors_pipeline.py` → `self.classifier_service.load_work_types(df)`
  - `app/pipelines/risks_pipeline.py` → `self.classifier_service.load_project_names(df)`
  - `app/pipelines/errors_pipeline.py` → `self.classifier_service.load_project_names(df)`
  - `app/pipelines/processes_pipeline.py` → `self.classifier_service.load_process_names(df)`

4) Логирование
- Логируется количество загруженных элементов и пример первых значений.
- Где: шаг «ШАГ 4: Загрузка элементов» в `BasePipeline.process()` и логи из `BaseClassifierService`.

## Выход
- Список доступных элементов (строки) в `classifier_service.items_list` — будет использоваться на шаге классификации.

## Ошибки и поведение
- Если колонки нет или элементы пусты — выдаётся предупреждение, `items_list` остаётся пустым.
- На шаге 5 (классификация) пустой `items_list` приведёт к раннему «пустому» ответу без ошибок.

## Где в коде
- Оркестрация шага: `app/pipelines/base.py` ("ШАГ 4: Загрузка элементов").
- Сервисы классификации (конкретные домены):
  - Подрядчики — `app/services/contractor_classifier.py`
  - Риски — `app/services/risk_classifier.py`
  - Ошибки — `app/services/error_classifier.py`
  - Процессы — `app/services/process_classifier.py`
- База: `app/services/base_classifier.py` (`load_items`, `get_column_name`, `_get_*_fallback`).
- Конфигурация колонок/типов: `ClassificationConfig` в `app/config.py` (используется в конструкторе `BaseClassifierService(entity_type=...)`).
- Место интеграции сервиса в пайплайн: фабрики DI в `app/pipelines/__init__.py` регистрируют и передают соответствующий `*ClassifierService` при создании пайплайна.

## Почему так
- Конфигурируемость: домены задают колонку и «тип элемента» через конфигурацию, без переписывания логики.
- Надёжность: отсутствие данных не ломает пайплайн — просто ведёт к корректному пустому ответу.
