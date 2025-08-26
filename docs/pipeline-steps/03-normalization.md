# Шаг 2: Нормализация данных (внутри контура пайплайна)

## Вход
- DataFrame: результат шага «Загрузка, очистка и информация о файле».
- button: тип кнопки (`contractors | risks | errors | processes`) — определяет профиль нормализации.

## Что происходит внутри
1) Переименование колонок
- По домену применяется маппинг «как назвать колонки по-единому».
- Где: `...NormalizationService.get_column_mapping()`.

2) Базовая нормализация текста
- Для всех строковых колонок: `fillna("")` → `strip()` → сжатие множественных пробелов до одного.
- Где: `BaseNormalizationService.clean_df()`.

3) Доменно-специфичные дополнения
- Опционально: выполняется только если в конкретном сервисе есть специализированные методы (например, `_additional_processing`).
- Пример (Risks): из JSON-строки в колонке `risk_json` извлекается чистый текст риска в `risk_text` (ключ `original`). Ошибки парсинга безопасно игнорируются (возвращается исходная строка).
- Где: `RiskNormalizationService._additional_processing()` и `_extract_risk_text()`.

4) Логирование
- Логируются: старт/конец нормализации, итоговые колонки.
- Где: `BaseNormalizationService.clean_df()` + общий `PipelineLogger`.

## Выход (единые схемы колонок)
- Contractors: `name, work_types, contact_person, contacts, website, projects, comments, primary_info, staff_size`.
- Risks: `project_id, project_type, project_name, risk_json, risk_priority, status, probability, severity, measures, risk_text`.
- Errors: `date, responsible, subject, description, measures, reason, project, stage, category`.
- Processes: `id, name, description, json_file, text_description`.

## Ошибки и поведение
- Отсутствующие исходные колонки не ломают процесс — переименовываются только существующие.
- Нормализация не читает файлы и не вызывает LLM; это быстрый и детерминированный шаг.

## Где в коде
- Оркестрация: `app/pipelines/base.py` ("ШАГ 2: Нормализация данных").
- База: `app/services/base_normalization.py` (`clean_df`).
- Доменные профили: 
  - У каждого пайплайна — свой сервис нормализации.
  - Подрядчики — `app/services/contractor_normalization.py` (класс `ContractorNormalizationService`).
  - Риски — `app/services/risk_normalization.py` (`RiskNormalizationService`).
  - Ошибки — `app/services/error_normalization.py` (`ErrorNormalizationService`).
  - Процессы — `app/services/process_normalization.py` (`ProcessNormalizationService`).

## Почему так
- Единообразие: дальнейшие шаги видят одинаковые имена колонок в любом домене.
- Предсказуемость: минимально необходимая очистка делается здесь, а доменная логика — дальше.
