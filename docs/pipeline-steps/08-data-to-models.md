# Шаг 7: Преобразование в модели (внутри контура пайплайна)

## Вход
- final_df: DataFrame после умной фильтрации (результат шага 6.5).
- final_scores: Dict[int, float] с оценками релевантности (индекс строки → оценка).
- Доменный пайплайн с реализованным методом `_create_model_instance()`.

## Что происходит внутри
1) Инициализация преобразования
- Определяется название сущности для логирования через `self._get_entity_name()`:
  - ContractorsPipeline → "подрядчиков"
  - RisksPipeline → "рисков" 
  - ErrorsPipeline → "ошибок"
  - ProcessesPipeline → "процессов"
- Логируется начало преобразования с количеством строк
- Где: `BasePipeline._dataframe_to_models()` → `app/pipelines/base.py:351-375`

2) Итерация по строкам DataFrame
- Для каждой строки `(idx, row)` в `final_df.iterrows()`:
  - Извлекается оценка релевантности: `relevance_scores.get(idx)` 
  - Вызывается доменный метод: `self._create_model_instance(row, relevance_score)`
  - Созданная модель добавляется в список `items`
- При ошибке преобразования конкретной записи — логируется WARNING, но процесс продолжается
- Где: `BasePipeline._dataframe_to_models()` → цикл на строках 363-368

3) Доменное преобразование строк в модели
Каждый пайплайн реализует собственный `_create_model_instance()`:

**ContractorsPipeline** (`app/pipelines/contractors_pipeline.py:43-62`):
```python
return Contractor(
    name=row.get('name', ''),
    work_types=row.get('work_types', ''),
    contact_person=row.get('contact_person', ''),
    contacts=row.get('contacts', ''),
    website=row.get('website', ''),
    projects=row.get('projects', ''),
    comments=row.get('comments', ''),
    primary_info=row.get('primary_info', ''),
    staff_size=row.get('staff_size', ''),
    relevance_score=relevance_score
)
```

**RisksPipeline** (`app/pipelines/risks_pipeline.py:45-58`):
```python
return Risk(
    project_id=str(row.get('project_id', '')),
    project_type=row.get('project_type', ''),
    project_name=row.get('project_name', ''),
    risk_text=row.get('risk_text', ''),
    risk_priority=row.get('risk_priority', ''),
    status=row.get('status', ''),
    measures=row.get('measures', ''),
    relevance_score=relevance_score
)
```

Аналогично для ErrorsPipeline и ProcessesPipeline с соответствующими моделями.

4) Сортировка по релевантности
- Если есть оценки релевантности (`final_scores` не пуст):
  - Модели сортируются по убыванию: `items.sort(key=lambda x: getattr(x, 'relevance_score', 0) or 0, reverse=True)`
  - Самые релевантные записи оказываются в начале списка
- Если оценок нет — порядок остается как в DataFrame
- Где: `BasePipeline._dataframe_to_models()` → строки 371-372

5) Валидация моделей через Pydantic
- При создании каждой модели автоматически происходит:
  - Валидация типов данных согласно схеме модели
  - Проверка обязательных полей
  - Приведение типов (например, `str(row.get('project_id', ''))`)
  - Установка значений по умолчанию для Optional полей
- Модели определены в: `app/domain/models/*.py`

6) Логирование результатов
- Количество успешно преобразованных моделей
- Предупреждения о строках, которые не удалось преобразовать
- Финальный счётчик созданных объектов
- Где: `BasePipeline._dataframe_to_models()` + логи в `_create_model_instance()`

## Выход
- items: List[BaseModel] — список типизированных объектов домена (Contractor/Risk/Error/Process)
- Модели отсортированы по релевантности (если есть оценки)
- Каждая модель содержит поле `relevance_score: Optional[float]`

## Ошибки и поведение
- Ошибка при создании конкретной модели → WARNING в логи, модель пропускается
- Некорректные данные в DataFrame → Pydantic может привести к типу или использовать значения по умолчанию
- Пустой DataFrame → возвращается пустой список, не ошибка
- Отсутствие оценок релевантности → модели остаются в порядке DataFrame

## Где в коде
- **Оркестрация шага**: `app/pipelines/base.py:260-272` ("ШАГ 7: Преобразование в модели")
- **Основная логика**: `app/pipelines/base.py:351-375` (`_dataframe_to_models()`)
- **Доменные реализации**: 
  - `app/pipelines/contractors_pipeline.py:43-62` (`_create_model_instance()`)
  - `app/pipelines/risks_pipeline.py:45-58` (`_create_model_instance()`)
  - `app/pipelines/errors_pipeline.py:XX-XX` (`_create_model_instance()`)
  - `app/pipelines/processes_pipeline.py:XX-XX` (`_create_model_instance()`)
- **Модели домена**:
  - `app/domain/models/contractor.py` (Contractor)
  - `app/domain/models/risk.py` (Risk)  
  - `app/domain/models/error.py` (Error)
  - `app/domain/models/process.py` (Process)

## Архитектурные особенности
- **Template Method Pattern**: `BasePipeline` определяет алгоритм, пайплайны реализуют `_create_model_instance()`
- **Pydantic валидация**: автоматическая проверка и приведение типов на уровне моделей
- **Graceful degradation**: ошибки отдельных записей не ломают весь пайплайн
- **Релевантность**: поддержка сортировки по оценкам из предыдущих шагов (особенно важно после умной фильтрации)

## Почему так
- **Типобезопасность**: Pydantic модели гарантируют корректную структуру данных для API
- **Разделение ответственности**: каждый пайплайн знает только свою доменную модель
- **Универсальность**: базовая логика в `BasePipeline`, специфика в наследниках
- **Сортировка**: важна для показа самых релевантных результатов пользователю в первую очередь
- **Отказоустойчивость**: частичные ошибки не приводят к полному провалу обработки запроса