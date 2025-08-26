# Добавление нового типа данных в DUP AI

## Что нужно создать

### 1. Модель домена
`app/domain/models/your_entity.py`
```python
from pydantic import BaseModel
from typing import Optional

class YourEntity(BaseModel):
    """Модель для новых данных."""
    id: str
    name: str
    category: str  # колонка для классификации
    description: Optional[str] = None
    relevance_score: Optional[float] = None
```

### 2. Enum для кнопки
`app/domain/enums.py` - добавить:
```python
class ButtonType(str, Enum):
    CONTRACTORS = "contractors"
    RISKS = "risks" 
    ERRORS = "errors"
    PROCESSES = "processes"
    YOUR_TYPE = "your_type"  # ДОБАВИТЬ
```

### 3. Конфигурация в config.py
```python
# Класс настроек
class YourTypeSettings(BaseAppSettings):
    model_config = ConfigDict(
        env_file='.env',
        extra='allow',
        env_prefix='YOURTYPE_'
    )
    data_file_path: str
    max_results: int = 20

# Экземпляр настроек
your_type_settings = YourTypeSettings()

# Конфигурация классификации
YOURTYPE = {
    "column_name": "category",  # по какой колонке классифицировать
    "item_type": "категория",   # как называть в промптах LLM
    "description": "Классификация по категориям"
}

# Стратегия умной фильтрации
strategy: Dict[str, str] = {
    # существующие...
    "your_type": "none",  # или "keybert"/"llm"/"both"
}
```

### 4. Переменные в .env
```env
YOURTYPE_DATA_FILE_PATH=./data/your_data.xlsx
YOURTYPE_MAX_RESULTS=20
```

### 5. Сервис нормализации
`app/services/your_type_normalization.py`
```python
from app.services.base_normalization import BaseNormalizationService

class YourTypeNormalizationService(BaseNormalizationService):
    def get_column_mapping(self) -> Dict[str, str]:
        return {
            'Excel_Column_1': 'id',
            'Excel_Column_2': 'name', 
            'Excel_Column_3': 'category',
            'Excel_Column_4': 'description'
        }
```

### 6. Сервис классификации
`app/services/your_type_classifier.py`
```python
from app.services.base_classifier import BaseClassifierService

class YourTypeClassifierService(BaseClassifierService):
    def __init__(self, llm_client: LLMClient):
        super().__init__(llm_client, entity_type="YOURTYPE")
    
    def load_categories(self, df: pd.DataFrame):
        """Загружает категории для классификации."""
        self.load_items(df)
    
    def filter_items(self, df: pd.DataFrame, category: str):
        """Фильтрует по выбранной категории."""
        return self.filter_items(df, category)
```

### 7. Сервис генерации ответов
`app/services/your_type_answer_generator.py`
```python
from app.services.base_answer_generator import BaseAnswerGeneratorService

class YourTypeAnswerGeneratorService(BaseAnswerGeneratorService):
    def _convert_item_to_dict(self, item: YourEntity) -> Dict[str, Any]:
        return {
            "id": item.id,
            "name": item.name,
            "category": item.category,
            "description": item.description,
            "relevance_score": item.relevance_score
        }
    
    def _get_prompts(self, question: str, items_data: List[Dict[str, Any]], **kwargs) -> Dict[str, str]:
        # Используйте PromptBuilder или создайте собственные промпты
        return {
            "system": "Ты эксперт по анализу данных...",
            "user": f"Вопрос: {question}\nДанные: {items_data}"
        }
    
    def _generate_fallback_text(self, question: str, items: List[BaseModel], **kwargs) -> str:
        return f"Найдено {len(items)} элементов по вашему запросу."
```

### 8. Пайплайн
`app/pipelines/your_type_pipeline.py`
```python
from app.pipelines.base import BasePipeline
from app.domain.models.your_entity import YourEntity

class YourTypePipeline(BasePipeline):
    def __init__(self, excel_loader, normalization_service, classifier_service, 
                 answer_generator, tool_executor):
        super().__init__(
            excel_loader=excel_loader,
            normalization_service=normalization_service,
            classifier_service=classifier_service,
            answer_generator=answer_generator,
            button_type=ButtonType.YOUR_TYPE,
            tool_executor=tool_executor
        )
    
    def _create_model_instance(self, row: pd.Series, relevance_score: Optional[float]) -> YourEntity:
        return YourEntity(
            id=str(row.get('id', '')),
            name=row.get('name', ''),
            category=row.get('category', ''),
            description=row.get('description', ''),
            relevance_score=relevance_score
        )
    
    def _get_entity_name(self) -> str:
        return "элементов"  # для логирования
    
    def _load_classifier_items(self, df: pd.DataFrame):
        self.classifier_service.load_categories(df)
    
    def _filter_data(self, df: pd.DataFrame, item_value: str):
        return self.classifier_service.filter_items(df, item_value)
```

### 9. Регистрация в DI контейнере
`app/pipelines/__init__.py` - добавить:
```python
# Импорты
from app.services.your_type_normalization import YourTypeNormalizationService
from app.services.your_type_classifier import YourTypeClassifierService  
from app.services.your_type_answer_generator import YourTypeAnswerGeneratorService
from app.pipelines.your_type_pipeline import YourTypePipeline

# В BUTTON_TO_PIPELINE
BUTTON_TO_PIPELINE: Dict[ButtonType, Type[Pipeline]] = {
    # существующие...
    ButtonType.YOUR_TYPE: YourTypePipeline,
}

# В init_container() добавить фабрики
container.register_factory(
    YourTypeNormalizationService,
    lambda: YourTypeNormalizationService()
)
container.register_factory(
    YourTypeClassifierService,
    lambda: YourTypeClassifierService(container.get(LLMClient))
)
container.register_factory(
    YourTypeAnswerGeneratorService, 
    lambda: YourTypeAnswerGeneratorService(container.get(LLMClient))
)

# В pipeline_factories добавить
pipeline_factories = {
    # существующие...
    ButtonType.YOUR_TYPE: lambda: YourTypePipeline(
        excel_loader=container.get(ExcelLoader),
        normalization_service=container.get(YourTypeNormalizationService),
        classifier_service=container.get(YourTypeClassifierService),
        answer_generator=container.get(YourTypeAnswerGeneratorService),
        tool_executor=container.get(ToolExecutor)
    ),
}
```

### 10. Обновить модель Answer
`app/domain/models/answer.py`
```python
from app.domain.models.your_entity import YourEntity

class Answer(BaseModel):
    items: Union[
        List[Contractor], 
        List[Risk], 
        List[Error], 
        List[Process],
        List[YourEntity]  # ДОБАВИТЬ
    ]
```

### 11. Обновить endpoints.py
```python
# В BUTTON_PROCESSORS добавить
BUTTON_PROCESSORS = {
    # существующие...
    ButtonType.YOUR_TYPE: lambda pipeline, req: pipeline.process(req.question),
}

# В лимиты добавить
limits = {
    # существующие...
    ButtonType.YOUR_TYPE: your_type_settings.max_results,
}
```

### 12. Обновить excel_loader.py
```python
from app.config import your_type_settings

# В file_paths добавить
file_paths = {
    # существующие...
    ButtonType.YOUR_TYPE: (your_type_settings.data_file_path, "файл данных"),
}
```

### 13. Обновить base.py логирование
```python
# В _get_file_path_for_logging() добавить
file_paths = {
    # существующие...
    ButtonType.YOUR_TYPE: your_type_settings.data_file_path,
}
```

## Структура Excel файла

Создайте `data/your_data.xlsx` с колонками:
- Excel_Column_1 → маппится в 'id' 
- Excel_Column_2 → маппится в 'name'
- Excel_Column_3 → маппится в 'category' (для классификации)
- Excel_Column_4 → маппится в 'description'

## Тестирование

Добавить в `test_universal_pipeline.py` поддержку нового типа или создать отдельный тест.

## Итого изменений

**Новые файлы (5):**
- `app/domain/models/your_entity.py`
- `app/services/your_type_normalization.py` 
- `app/services/your_type_classifier.py`
- `app/services/your_type_answer_generator.py`
- `app/pipelines/your_type_pipeline.py`

**Изменения существующих (7):**
- `app/domain/enums.py` - добавить ButtonType
- `app/config.py` - настройки, классификация, стратегия
- `app/pipelines/__init__.py` - регистрация в DI
- `app/domain/models/answer.py` - добавить в Union
- `app/api/v1/endpoints.py` - процессор и лимиты
- `app/adapters/excel_loader.py` - путь к файлу
- `app/pipelines/base.py` - путь для логирования

**Конфигурация:**
- `.env` - переменные YOURTYPE_*
- `data/your_data.xlsx` - файл с данными