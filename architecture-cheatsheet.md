# Architecture Quick Reference

## Слои архитектуры

### 1. API Layer (Presentation)
- `endpoints.py` - обработка HTTP запросов
- `schemas.py` - валидация входных/выходных данных

### 2. Pipeline Layer (Application)
- Оркестрация бизнес-процессов
- Координация сервисов
- Обработка исключений

### 3. Service Layer (Business Logic)
- **Normalization** - очистка данных
- **Classifier** - классификация через LLM
- **AnswerGenerator** - генерация ответов

### 4. Domain Layer (Core)
- Доменные модели (Contractor, Risk, Error, Process)
- Бизнес-правила
- Перечисления (enums)

### 5. Adapter Layer (Infrastructure)
- `excel_loader.py` - работа с Excel файлами
- `llm_client.py` - интеграция с LLM

## Dependency Injection

```python
# Регистрация в контейнере
container.register_factory(
    ContractorClassifierService,
    lambda: ContractorClassifierService(container.get(LLMClient))
)

# Получение из контейнера
classifier = container.get(ContractorClassifierService)
```

## Паттерны

### 1. Factory Pattern
```python
# Создание пайплайнов
def get_pipeline(button_type: ButtonType) -> Pipeline:
    factories = {
        ButtonType.CONTRACTORS: create_contractors_pipeline,
        ButtonType.RISKS: create_risks_pipeline,
        # ...
    }
    return factories[button_type]()
```

### 2. Template Method Pattern
```python
# Базовый пайплайн с шаблонным методом
class BasePipeline:
    def process(self, question: str) -> Answer:
        # 1. Загрузка данных
        df = self.excel_loader.load()
        # 2. Нормализация
        cleaned_df = self.normalization_service.clean_df(df)
        # 3. Классификация
        best_item = self.classifier_service.classify(question)
        # 4. Фильтрация
        filtered_df = self.filter_data(df, best_item)
        # 5. Генерация ответа
        return self.answer_generator.make_md(question, filtered_df)
```

### 3. Strategy Pattern
```python
# Разные стратегии обработки для разных типов данных
BUTTON_PROCESSORS = {
    ButtonType.CONTRACTORS: process_contractors,
    ButtonType.RISKS: process_risks,
    # ...
}
```

## Поток данных

1. **Request** → `API Endpoint`
2. **Route** → выбор `Pipeline` по типу кнопки
3. **Load** → `ExcelLoader` загружает данные
4. **Normalize** → `NormalizationService` очищает
5. **Classify** → `ClassifierService` + `LLM`
6. **Filter** → фильтрация по результатам
7. **Generate** → `AnswerGenerator` + `LLM`
8. **Response** → возврат клиенту

## Конфигурация

### Иерархия настроек
```
BaseAppSettings
├── AppSettings (основные)
├── ContractorSettings
├── RiskSettings  
├── ErrorSettings
├── ProcessSettings
└── LLMSettings
```

### Префиксы переменных окружения
- `APP_` - основные настройки
- `CONTRACTOR_` - настройки подрядчиков и LLM
- `RISK_` - настройки рисков
- `ERROR_` - настройки ошибок
- `PROCESS_` - настройки процессов

## Логирование

```python
# Настройка логгера
from app.utils.logging import setup_logger
logger = setup_logger(__name__)

# Использование
logger.info("Сообщение")
logger.error(f"Ошибка: {e}")
logger.debug("Отладочная информация")
```

### Уровни логирования
- **Console**: INFO и выше
- **File**: DEBUG и выше

## Добавление нового типа данных

1. **Модель** → `app/domain/models/new_type.py`
2. **Enum** → добавить в `ButtonType`
3. **Сервисы**:
   - `new_type_normalization.py`
   - `new_type_classifier.py`
   - `new_type_answer_generator.py`
4. **Pipeline** → `new_type_pipeline.py`
5. **Регистрация** → в `pipelines/__init__.py`
6. **Конфигурация** → в `config.py` и `.env`

## Обработка ошибок

```python
try:
    # Основная логика
    result = pipeline.process(question)
except Exception as e:
    logger.error(f"Ошибка: {e}")
    return Answer(
        text=f"Ошибка: {str(e)}",
        query=question,
        total_found=0,
        items=[]
    )
```

## Советы по отладке

1. **Включить отладку промптов**:
   ```env
   LOG_PROMPTS=true
   ```

2. **Проверить LLM**:
   ```bash
   curl http://localhost:11434/api/tags
   ```

3. **Посмотреть логи**:
   ```bash
   tail -f LOGS/app.main.log
   ```

4. **Тестовый запрос**:
   ```bash
   curl http://localhost:8080/v1/health
   ```