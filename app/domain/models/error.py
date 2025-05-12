from pydantic import BaseModel
from typing import Optional

class Error(BaseModel):
    """Модель данных об ошибке проекта."""
    date: Optional[str] = None  # Дата фиксации
    responsible: Optional[str] = None  # Ответственный
    subject: Optional[str] = None  # Предмет ошибки
    description: str  # Описание ошибки
    measures: Optional[str] = None  # Предпринятые меры
    reason: Optional[str] = None  # Причина
    project: str  # Проект
    stage: Optional[str] = None  # Стадия проекта
    category: Optional[str] = None  # Категория
    relevance_score: Optional[float] = None  # Оценка релевантности