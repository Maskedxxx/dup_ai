from pydantic import BaseModel
from typing import List, Optional, Union
from app.domain.models.contractor import Contractor
from app.domain.models.risk import Risk
from app.domain.models.error import Error
from app.domain.models.process import Process

class Answer(BaseModel):
    """Модель финального ответа."""
    text: str  # Текст ответа
    query: str  # Исходный запрос
    total_found: int  # Общее количество найденных элементов
    items: Union[List[Contractor], List[Risk], List[Error], List[Process]]  # Список результатов (подрядчики, риски, ошибки, bpmn процессы)
    meta: Optional[dict] = None  # Дополнительные метаданные
    category: Optional[str] = None  # Категория (для рисков)