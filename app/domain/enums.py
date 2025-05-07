from enum import Enum, auto

class ButtonType(str, Enum):
    """Типы кнопок в интерфейсе."""
    CONTRACTORS = "contractors"
    RISKS = "risks"
    ERRORS = "errors"

class RiskCategory(str, Enum):
    """Типы категорий рисков."""
    NIOKR = "niokr"
    PRODUCT_PROJECT = "product_project"
    MANUFACTURING = "manufacturing"