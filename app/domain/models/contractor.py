from pydantic import BaseModel
from typing import Optional

class Contractor(BaseModel):
    """Модель данных о подрядчике."""
    name: str  # Наименование КА
    work_types: str  # Виды работ
    contact_person: Optional[str] = None  # Контактное лицо
    contacts: Optional[str] = None  # Контакты
    website: Optional[str] = None  # Сайт
    projects: Optional[str] = None  # Задействован в проекте
    comments: Optional[str] = None  # Комментарий
    primary_info: Optional[str] = None  # Первичная информация
    staff_size: Optional[str] = None  # Штат
    relevance_score: Optional[float] = None  # Оценка релевантности