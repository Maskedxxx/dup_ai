# app/domain/models/risk.py

from pydantic import BaseModel
from typing import Optional, Dict, Any

class Risk(BaseModel):
    """Модель данных о риске проекта."""
    project_id: str  # № проекта
    project_type: str  # Тип проекта
    project_name: str  # Наименование проекта
    risk_text: str  # Текст риска (из JSON)
    risk_priority: Optional[str] = None  # Приоритетность
    status: Optional[str] = None  # Текущий статус
    relevance_score: Optional[float] = None  # Оценка релевантности