# app/api/v1/schemas.py

from pydantic import BaseModel
from typing import Optional, List, Union
from app.domain.enums import ButtonType, RiskCategory
from app.domain.models.contractor import Contractor
from app.domain.models.risk import Risk
from app.domain.models.error import Error
from app.domain.models.process import Process

class AskRequest(BaseModel):
    """Модель запроса для обработки вопроса."""
    question: str  # Вопрос пользователя
    button: ButtonType  # Тип кнопки
    risk_category: Optional[RiskCategory] = None  # Категория риска (только для button=risks)

class AskResponse(BaseModel):
    """Модель ответа на запрос."""
    text: str  # Текст ответа
    query: str  # Исходный запрос
    total_found: int  # Общее количество найденных элементов
    items: Union[List[Contractor], List[Risk], List[Error], List[Process]]  # Список результатов (подрядчики, риски, ошибки, bpmn процессы)
    meta: Optional[dict] = None  # Дополнительные метаданные
    category: Optional[str] = None  # Категория (для рисков)