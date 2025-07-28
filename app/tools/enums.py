# app/tools/enums.py

from enum import Enum


class ToolType(str, Enum):
    """
    Типы доступных инструментов для фильтрации данных.
    """
    KEYWORD_SEARCH = "keyword_search"