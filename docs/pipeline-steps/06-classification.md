# Шаг 5: Классификация вопроса (внутри контура пайплайна)

## Вход
- question: текст вопроса пользователя.
- items_list: список доступных элементов из шага 4 (проекты/виды работ/процессы и т.д.).
- item_type: человекочитаемый тип элемента (например, «проект», «вид работ», «процесс») — берётся из `ClassificationConfig`.

## Что происходит внутри
1) Подготовка списка для промпта
- Каждый элемент временно обрамляется разделителями `#` (например, `#Проект А#`). Это помогает LLM не «искажать» строку и точно выбирать из списка.
- Где: `BaseClassifierService._preprocess_items_with_hashtags()`.

2) Динамическая модель ответа
- На лету создаётся Pydantic‑модель с полем `item`, тип которого — `Literal[<#item1#>, <#item2#>, ...]`, и `score: float`.
- Итоговая модель: `{ reasoning: str, top_matches: List[{item, score}] }` (1–3 варианта).
- Где: `BaseClassifierService._create_dynamic_classification_model()`.

3) Построение промптов
- Генерируются system/user промпты с инструкциями и форматами ответа; в список подставляются элементы с `#`.
- Где: `BaseClassifierService._build_classification_prompts()` → `PromptBuilder.build_classification_prompt()`.

4) Вызов LLM со структурированным ответом
- Вызов клиента: `LLMClient.generate_structured_completion(...)` с `response_model` из шага 2, `temperature=0`.
- Результат парсится сразу в Pydantic‑модель, без ручного `json.loads`.
- Где: `app/adapters/llm_client.py` (`beta.chat.completions.parse`, OpenAI‑совместимый клиент к Ollama).

5) Выбор лучшего соответствия
- Берём `top_matches`, логируем `reasoning` и все варианты; выбираем `max(score)`.
- Удаляем `#`‑разделители и получаем «чистое» значение элемента.
- Где: `BaseClassifierService.classify()`.

6) Логирование
- В debug‑режиме логируются полный system/user промпты и ответ модели.
- Где: `PipelineLogger.log_prompt_details(...)`.

## Выход
- best_item: строка — лучший элемент из `items_list`, на который «указывает» вопрос.
- Если определить нельзя (пустой список/ошибка LLM/неструктурированный ответ) — возвращается пустая строка `""` (пайплайн сформирует корректный «пустой» ответ позже).

## Ошибки и поведение
- Пустой `items_list` → ранний выход без вызова LLM.
- Любая ошибка LLM/парсинга → логируется, возвращается `""`.
- Температура = 0 для стабильного выбора.

## Где в коде
- Логика шага: `app/services/base_classifier.py` (`classify`, `_preprocess_items_with_hashtags`, `_create_dynamic_classification_model`, `_build_classification_prompts`).
- Промпты: `app/utils/prompt_builder.py`.
- LLM‑клиент: `app/adapters/llm_client.py` (`generate_structured_completion`).

## Почему так
- Точность: `Literal[...]` + `#...#` режут «творчество» модели и удерживают её в рамках заданного списка.
- Простота интеграции: результат сразу валидируется и парсится в Pydantic‑модель.
- Прозрачность: все ключевые шаги и промпты прозрачно логируются в debug‑режиме.

