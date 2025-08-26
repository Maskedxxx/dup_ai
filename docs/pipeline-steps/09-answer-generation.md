# Шаг 8: Генерация ответа (внутри контура пайплайна)

## Вход
- question: исходный вопрос пользователя.
- items: List[BaseModel] — типизированные модели домена после шага 7.
- additional_context: строка с дополнительным контекстом (результат `_generate_additional_context()`).
- **kwargs: дополнительные параметры (category для рисков, meta и др.).

## Что происходит внутри
1) Генерация дополнительного контекста
- Вызывается доменный метод `_generate_additional_context(filtered_df, best_item, **kwargs)`:
  - ContractorsPipeline → `"Найдено {count} подрядчиков для типа работ '{best_item}'"`
  - RisksPipeline → `"Найдено {count} рисков для проекта '{best_item}' в категории '{risk_category}'"`
  - ErrorsPipeline → `"Найдено {count} ошибок для проекта '{best_item}'"`
  - ProcessesPipeline → `"Найдено {count} процессов для '{best_item}'"`
- Контекст содержит краткую статистику найденных элементов
- Где: `BasePipeline.process()` → строка 277 → доменные реализации в пайплайнах

2) Вызов генератора ответов
- Используется доменный `answer_generator` (DI из контейнера):
  - ContractorsPipeline → `AnswerGeneratorService`
  - RisksPipeline → `RiskAnswerGeneratorService`
  - ErrorsPipeline → `ErrorAnswerGeneratorService`
  - ProcessesPipeline → `ProcessAnswerGeneratorService`
- Вызов: `self.answer_generator.make_md(question, items, additional_context, **kwargs)`
- Где: `BasePipeline._generate_answer()` → строка 344-349

3) Преобразование моделей в промпт-данные
- Каждый элемент из `items` преобразуется в словарь через доменный `_convert_item_to_dict()`:

**RiskAnswerGeneratorService** (`app/services/risk_answer_generator.py:19-35`):
```python
{
    "project_name": item.project_name,
    "risk_text": item.risk_text,
    "risk_priority": item.risk_priority,
    "status": item.status,
    "measures": item.measures,
    "project_id": item.project_id,
    "project_type": item.project_type,
    "relevance_score": item.relevance_score
}
```

Аналогично для других типов с соответствующими полями.
- Где: `BaseAnswerGeneratorService.make_md()` → строки 82-90

4) Построение промптов для LLM
- Вызывается доменный метод `_get_prompts(question, items_data, **kwargs)`:
  - Возвращает словарь: `{"system": "...", "user": "..."}`
  - Использует `PromptBuilder` для создания структурированных промптов
  - Включает дополнительный контекст, категорию (для рисков) и другие параметры
- Для логирования создается усеченная версия (первые 5 элементов), чтобы избежать переполнения логов
- Где: `BaseAnswerGeneratorService.make_md()` → строки 98, 104

5) Вызов LLM для генерации текста
- Используется `LLMClient.generate_completion()`:
  - `system_prompt` — инструкции для модели
  - `user_prompt` — вопрос и данные для анализа
  - `temperature=0.2` — небольшая креативность для человечного ответа
- Где: `BaseAnswerGeneratorService.make_md()` → строки 120-124 → `app/adapters/llm_client.py`

6) Создание финальной модели Answer
- Формируется экземпляр `Answer` с полями:
  - `text`: сгенерированный LLM текст ответа
  - `query`: исходный вопрос пользователя  
  - `total_found`: количество найденных элементов (`len(items)`)
  - `items`: список доменных моделей для API
  - `meta`: дополнительные метаданные (опционально)
  - `category`: категория для рисков (опционально)
- Где: `BaseAnswerGeneratorService.make_md()` → строки 139-146

7) Детальное логирование процесса
- **Начальная информация**: вопрос, количество элементов
- **Промпт-детали** (в DEBUG режиме):
  - Полные system/user промпты (урезанные если > 5 элементов)
  - LLM ответ с длиной текста
- **Статистика генерации**: успех/ошибка, длина результата
- Где: `BaseAnswerGeneratorService.make_md()` + `PipelineLogger.log_prompt_details()`

8) Обработка ошибок (Fallback)
- При любой ошибке LLM вызывается доменный `_generate_fallback_text()`:
  - Создается базовый ответ без использования LLM
  - Основан на количестве и типе найденных элементов
  - Гарантирует, что пользователь всегда получит ответ
- Возвращается Answer с fallback текстом, но теми же найденными `items`
- Где: `BaseAnswerGeneratorService.make_md()` → строки 151-156

## Выход
- answer: модель `Answer` с полями:
  - `text`: человеко-читаемый ответ на вопрос (Markdown)
  - `query`: исходный запрос пользователя
  - `total_found`: общее количество найденных элементов
  - `items`: список доменных моделей для дальнейшего использования API
  - `meta`: дополнительные метаданные
  - `category`: категория риска (если применимо)

## Ошибки и поведение
- Ошибка преобразования элемента в словарь → WARNING, элемент пропускается
- Ошибка LLM (сеть, модель, превышение лимитов) → автоматический fallback ответ
- Пустой список `items` → корректный ответ "не найдено элементов"
- Все ошибки логируются, но не прерывают пайплайн

## Где в коде
- **Оркестрация шага**: `app/pipelines/base.py:274-287` ("ШАГ 8: Генерация ответа")
- **Генерация контекста**: доменные `_generate_additional_context()` в пайплайнах
- **Делегирование**: `app/pipelines/base.py:340-349` (`_generate_answer()`)
- **Базовая логика**: `app/services/base_answer_generator.py:67-160` (`make_md()`)
- **Доменные генераторы**:
  - `app/services/contractor_answer_generator.py` (AnswerGeneratorService)
  - `app/services/risk_answer_generator.py` (RiskAnswerGeneratorService)  
  - `app/services/error_answer_generator.py` (ErrorAnswerGeneratorService)
  - `app/services/process_answer_generator.py` (ProcessAnswerGeneratorService)
- **Промпты**: `app/utils/prompt_builder.py` (PromptBuilder.build_answer_prompt)
- **LLM клиент**: `app/adapters/llm_client.py` (generate_completion)
- **Модель ответа**: `app/domain/models/answer.py` (Answer)

## Доменная специализация
Каждый тип данных имеет собственные особенности:

**Риски** (`RiskAnswerGeneratorService`):
- Включает `risk_category` в промпты для более точного контекста
- Специализированные поля: priority, status, measures
- Поддержка релевантности от умной фильтрации

**Подрядчики** (`AnswerGeneratorService`):
- Фокус на типах работ, контактной информации, проектах
- Простая структура без дополнительной категоризации

**Ошибки/Процессы**: аналогично с соответствующими доменными полями

## Архитектурные особенности
- **Template Method Pattern**: базовый алгоритм в `BaseAnswerGeneratorService`, доменные детали в наследниках
- **Fallback механизм**: гарантированный ответ даже при сбоях LLM
- **Оптимизированное логирование**: урезание больших промптов для читаемости логов
- **Низкая temperature**: баланс между точностью и естественностью ответа
- **Типизированные модели**: Answer содержит Union типы для строгой валидации API

## Почему так
- **Доменная экспертиза**: каждый генератор знает специфику своих данных и промптов
- **Отказоустойчивость**: fallback гарантирует ответ пользователю при любых условиях
- **Прозрачность**: детальное логирование промптов помогает в отладке качества ответов LLM
- **Производительность**: умное логирование предотвращает переполнение логов большими данными
- **Расширяемость**: легко добавить новые типы генераторов с собственной логикой промптов