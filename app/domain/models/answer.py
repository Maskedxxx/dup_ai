from pydantic import BaseModel
from typing import List, Optional, Union
from app.domain.models.contractor import Contractor
from app.domain.models.risk import Risk

class Answer(BaseModel):
    """Модель финального ответа."""
    text: str  # Текст ответа
    query: str  # Исходный запрос
    total_found: int  # Общее количество найденных элементов
    items: Union[List[Contractor], List[Risk]]  # Список результатов (подрядчики или риски)
    meta: Optional[dict] = None  # Дополнительные метаданные
    category: Optional[str] = None  # Категория (для рисков)