# Кратко: как работает приложение

## Что это
- Ответы на ваши вопросы по данным: подрядчики, риски, ошибки, процессы. Нажимаете кнопку, пишете вопрос — получаете ясный ответ.

## Как пользоваться
- Выберите кнопку: contractors, risks, errors, processes.
- Напишите вопрос простыми словами.
- Нажмите «Отправить» и подождите ответ.

## Что происходит внутри (простыми словами + где в коде)
1) Приём запроса
   - Что: сервер получает кнопку и ваш текст.
   - Код: `POST /v1/ask` в `app/api/v1/endpoints.py` (модели `AskRequest`, `AskResponse` в `app/api/v1/schemas.py`).

2) Выбор пайплайна
   - Что: выбираем «линию обработки» под кнопку.
   - Код: `get_pipeline(button)` в `app/pipelines/__init__.py` создаёт нужный класс: Contractors/Risks/Errors/Processes, собирая зависимости из DI-контейнера `app/config.py`.

3) Загрузка данных
   - Что: берём таблицу из Excel, соответствующую кнопке.
   - Код: `ExcelLoader.load(button_type)` в `app/adapters/excel_loader.py` (пути к файлам в `.env`, читаются через `app/config.py`).

4) Нормализация
   - Что: аккуратно чистим текст в колонках, приводим формат к единому виду.
   - Код: соответствующий `...NormalizationService` в `app/services/*_normalization.py` (вызов на шаге 2 пайплайна `BasePipeline` в `app/pipelines/base.py`).

5) Понимание задачи (классификация)
   - Что: ИИ определяет, к чему именно относится ваш вопрос (например, к какому проекту/виду работ).
   - Код: `...ClassifierService.classify()` в `app/services/base_classifier.py`:
     - Готовит промпт через `PromptBuilder` (`app/utils/prompt_builder.py`),
     - Вызывает модель через `LLMClient` (`app/adapters/llm_client.py`, OpenAI-совместимый клиент к Ollama),
     - Выбирает «лучший» элемент из списка.

6) Отбор данных
   - Что: из таблицы оставляем строки по выбранному элементу.
   - Код: `filter_items()` в `app/services/base_classifier.py` (шаг 6 в `BasePipeline`).

6.5) Умная фильтрация (для рисков)
   - Что: дополнительно отсеиваем нерелевантное по ключевым словам.
   - Код: `ToolExecutor.apply_smart_filtering()` в `app/tools/tool_executor.py`:
     - Стратегия из `app/config.py` → для `risks` используется `keybert`,
     - Ключевые слова извлекает `KeyBERTService` (`app/services/keybert_service.py`),
     - Поиск по словам — `KeywordSearchTool` (`app/tools/implementations/_shared/keyword_search_tool.py`).

7) Преобразование в модели
   - Что: превращаем строки в понятные сущности (Подрядчик/Риск/Ошибка/Процесс).
   - Код: модели в `app/domain/models/*.py` (шаг 7 в `BasePipeline`).

8) Генерация ответа
   - Что: собираем человеческий ответ на основе отобранных данных.
   - Код: `...AnswerGeneratorService.make_md()` в `app/services/*_answer_generator.py`:
     - Строит промпт через `PromptBuilder`,
     - Вызывает LLM через `LLMClient`,
     - Возвращает `Answer` (текст + список найденных элементов).

9) Возврат клиенту
   - Что: отправляем финальный ответ и данные.
   - Код: `endpoints.py` формирует `AskResponse`, обрезает `items` по `limit` и отдаёт JSON.

## Кнопки (что означает каждая)
- Contractors: факты о подрядчиках и видах работ.
- Risks: список рисков, умная фильтрация по ключевым словам.
- Errors: найденные ошибки и описания.
- Processes: описание бизнес-процессов.

## Логи и настройки
- Логи: человекочитаемые шаги пайплайна в `LOGS/dup_ai.log` (`app/utils/logging.py`).
- Настройки: `.env` (пути к Excel, LLM и пр.), читаются через `app/config.py`.

## Пример
- Нажмите «risks», введите: «какие риски в разделе закупок?», отправьте — получите короткий список рисков с приоритетом и пояснениями.

