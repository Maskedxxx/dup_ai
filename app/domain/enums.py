from enum import Enum, auto

class ButtonType(str, Enum):
    """Типы кнопок в интерфейсе."""
    CONTRACTORS = "contractors"
    RISKS = "risks"
    # Другие типы кнопок можно добавить здесь

class RiskCategory(str, Enum):
    """Типы категорий рисков."""
    NIOKR = "niokr"
    PRODUCT_PROJECT = "product_project"
    MANUFACTURING = "manufacturing"