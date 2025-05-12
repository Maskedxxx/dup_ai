from pydantic import BaseModel
from typing import Optional

class Process(BaseModel):
    """Модель данных о бизнес-процессе."""
    id: str  # ID
    name: str  # Название процесса
    description: Optional[str] = None  # Описание
    json_file: Optional[str] = None  # Файл JSON
    text_description: Optional[str] = None  # Текстовое описание
    relevance_score: Optional[float] = None  # Оценка релевантности