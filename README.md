# Contractor Analysis API

API для анализа данных о подрядчиках, рисках проектов, ошибках и бизнес-процессах с использованием LLM.

## Архитектура

Приложение построено по принципам чистой архитектуры (Clean Architecture):

```
┌─────────────────────────────────────────────────────────────┐
│                        API Layer                            │
│                   (FastAPI endpoints)                       │
├─────────────────────────────────────────────────────────────┤
│                    Pipeline Layer                           │
│              (Orchestration & Flow)                         │
├─────────────────────────────────────────────────────────────┤
│                    Service Layer                            │
│        (Business Logic & Processing)                        │
├─────────────────────────────────────────────────────────────┤
│                    Domain Layer                             │
│              (Models & Business Rules)                      │
├─────────────────────────────────────────────────────────────┤
│                   Adapter Layer                             │
│           (External Services & Data)                        │
└─────────────────────────────────────────────────────────────┘
```

## Основные компоненты

### 1. API Layer (`app/api/`)
- **endpoints.py** - REST API эндпоинты
- **schemas.py** - Pydantic модели для валидации запросов/ответов

### 2. Pipeline Layer (`app/pipelines/`)
- **base.py** - Базовый класс для всех пайплайнов
- **contractors_pipeline.py** - Обработка запросов о подрядчиках
- **risks_pipeline.py** - Обработка запросов о рисках
- **errors_pipeline.py** - Обработка запросов об ошибках проектов  
- **processes_pipeline.py** - Обработка запросов о бизнес-процессах

### 3. Service Layer (`app/services/`)
Каждый тип данных имеет 3 сервиса:
- **Normalization** - нормализация данных из Excel
- **Classifier** - классификация запросов с помощью LLM
- **AnswerGenerator** - генерация ответов с помощью LLM

### 4. Domain Layer (`app/domain/`)
- **models/** - доменные модели (Contractor, Risk, Error, Process)
- **enums.py** - перечисления (ButtonType, RiskCategory)

### 5. Adapter Layer (`app/adapters/`)
- **excel_loader.py** - загрузка данных из Excel
- **llm_client.py** - интеграция с LLM (Ollama)

## Поток данных

1. **Запрос от клиента** → API endpoint
2. **Выбор пайплайна** по типу кнопки (contractors/risks/errors/processes)
3. **Загрузка данных** из Excel файла
4. **Нормализация** - очистка и стандартизация данных
5. **Классификация** - определение релевантных элементов через LLM
6. **Фильтрация** - отбор данных по результатам классификации
7. **Генерация ответа** - создание ответа через LLM
8. **Возврат ответа** клиенту

## Быстрый старт

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Настройка конфигурации
```bash
cp .env.example .env
# Отредактируйте .env файл
```

### 3. Подготовка данных
Поместите Excel файлы в директорию `data/`:
- `contractors.xlsx` - данные о подрядчиках
- `riski.xlsx` - данные о рисках проектов
- `errors.xlsx` - данные об ошибках
- `bpmn_processes.xlsx` - данные о бизнес-процессах

### 4. Запуск приложения
```bash
uvicorn app.main:app --reload
```

### 5. Проверка работы
```bash
curl http://localhost:8080/v1/health 
```

## API Документация

### POST /v1/ask
Основной эндпоинт для обработки запросов.

**Request:**
```json
{
  "question": "Найди подрядчиков для строительства дорог",
  "button": "contractors",
  "risk_category": null  // только для button="risks"
}
```

**Response:**
```json
{
  "text": "Сгенерированный ответ от LLM",
  "query": "Исходный запрос",
  "total_found": 5,
  "items": [...],  // Список найденных элементов
  "meta": {},
  "category": null
}
```

### Типы кнопок:
- `contractors` - поиск подрядчиков
- `risks` - анализ рисков проектов
- `errors` - анализ ошибок проектов
- `processes` - поиск бизнес-процессов

### Категории рисков:
- `niokr` - НИОКР проекты
- `product_project` - продуктовые проекты
- `manufacturing` - производственные проекты

## Конфигурация

### Переменные окружения (.env)

```env
# Приложение
APP_NAME=Contractor Analysis API
DEBUG=true
HOST=0.0.0.0
PORT=8080

# LLM настройки
CONTRACTOR_OLLAMA_BASE_URL=http://localhost:11434/v1
CONTRACTOR_OLLAMA_MODEL=llama3.1:8b-instruct-fp16

# Пути к данным
CONTRACTOR_DATA_FILE_PATH=./data/contractors.xlsx
RISK_DATA_FILE_PATH=./data/riski.xlsx
ERROR_DATA_FILE_PATH=./data/errors.xlsx
PROCESS_DATA_FILE_PATH=./data/bpmn_processes.xlsx

# Лимиты
CONTRACTOR_MAX_RESULTS=20
RISK_MAX_RESULTS=20
```

## Логирование

Логи сохраняются в директорию `LOGS/` с ротацией файлов:
- Консоль: INFO и выше
- Файлы: DEBUG и выше

Пример настройки логгера:
```python
from app.utils.logging import setup_logger
logger = setup_logger(__name__)
```

## Добавление нового типа данных

1. Создайте модель в `app/domain/models/`
2. Добавьте новый тип в `ButtonType` enum
3. Создайте 3 сервиса в `app/services/`:
   - `{type}_normalization.py`
   - `{type}_classifier.py` 
   - `{type}_answer_generator.py`
4. Создайте пайплайн в `app/pipelines/{type}_pipeline.py`
5. Зарегистрируйте в `app/pipelines/__init__.py`
6. Добавьте настройки в `app/config.py` и `.env`

## Решение проблем

### LLM не отвечает
- Проверьте доступность Ollama: `curl http://localhost:11434/api/tags`
- Убедитесь, что модель скачана: `ollama list`

### Ошибки загрузки данных
- Проверьте пути к файлам в `.env`
- Убедитесь, что Excel файлы имеют правильную структуру

### Отладка промптов
Включите логирование промптов:
```env
LOG_PROMPTS=true
```

## Примеры использования

### Python клиент
```python
import requests

response = requests.post(
    "http://localhost:8080/v1/ask",
    json={
        "question": "Какие подрядчики занимаются дорожным строительством?",
        "button": "contractors"
    }
)

data = response.json()
print(f"Найдено: {data['total_found']} подрядчиков")
print(data['text'])
```

### cURL
```bash
curl -X POST "http://localhost:8080/v1/ask" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "Риски для НИОКР проектов",
       "button": "risks",
       "risk_category": "niokr"
     }'
```

## Архитектурные решения

1. **Базовые классы** - минимизация дублирования кода
2. **Dependency Injection** - управление зависимостями через Container
3. **Фабричный паттерн** - создание пайплайнов
4. **Чистая архитектура** - независимость слоев
5. **Pydantic модели** - валидация данных
6. **Async/await** - асинхронная обработка запросов

## Контакты

При возникновении вопросов обращайтесь к автору проекта.