# app/tools/common_toolsets.py

from typing import List


class CommonToolSets:
    """
    Утилитарный класс для определения общих наборов инструментов.
    
    Позволяет избежать дублирования кода при определении наборов инструментов
    для разных пайплайнов, сохраняя при этом гибкость для кастомизации.
    
    Примеры использования:
    
    # Базовый набор
    def get_tool_names(self) -> List[str]:
        return CommonToolSets.BASIC_SEARCH
    
    # Расширенный набор с дополнительными инструментами
    def get_tool_names(self) -> List[str]:
        return CommonToolSets.RISK_ANALYSIS + ["custom_risk_validator"]
    
    # Комбинирование наборов
    def get_tool_names(self) -> List[str]:
        return CommonToolSets.combine(
            CommonToolSets.BASIC_SEARCH,
            ["date_filter", "priority_filter"]
        )
    """
    
    # Базовые наборы инструментов
    BASIC_SEARCH: List[str] = [
        "search_by_keywords"
    ]
    
    # РЕАЛЬНО РАБОТАЮЩИЕ НАБОРЫ
    RISK_ANALYSIS: List[str] = [
        "search_by_keywords"  # Единственный реально работающий инструмент
        # "filter_by_priority",  # Будущий инструмент для приоритетов
        # "date_range_filter"    # Будущий инструмент для дат
    ]
    
    # ЗАГОТОВКИ ДЛЯ БУДУЩИХ НАБОРОВ (пока пустые)
    CONTRACTOR_ANALYSIS: List[str] = [
        # Пока нет инструментов для подрядчиков
        # "location_filter",     # Будущий: поиск по регионам
        # "capacity_filter",     # Будущий: поиск по мощности  
        # "search_by_keywords"   # Добавится когда будет готов
    ]
    
    ERROR_ANALYSIS: List[str] = [
        # Пока нет инструментов для ошибок
        # "severity_filter",     # Будущий: фильтр по серьезности
        # "category_filter",     # Будущий: фильтр по категориям
        # "search_by_keywords"   # Добавится когда будет готов
    ]
    
    PROCESS_ANALYSIS: List[str] = [
        # Пока нет инструментов для процессов
        # "complexity_filter",   # Будущий: фильтр по сложности
        # "stage_filter",        # Будущий: фильтр по этапам
        # "search_by_keywords"   # Добавится когда будет готов
    ]
    
    # Специальные наборы
    FULL_ANALYSIS: List[str] = [
        "search_by_keywords"   # Пока только этот работает
        # Остальные инструменты добавятся по мере готовности
    ]
    
    NONE: List[str] = []  # Пустой набор для пайплайнов без инструментов
    
    @staticmethod
    def combine(*toolsets: List[str]) -> List[str]:
        """
        Объединяет несколько наборов инструментов, удаляя дубликаты.
        
        :param toolsets: Наборы инструментов для объединения
        :return: Объединенный список без дубликатов
        
        Пример:
            tools = CommonToolSets.combine(
                CommonToolSets.BASIC_SEARCH,
                ["custom_tool_1", "custom_tool_2"],
                CommonToolSets.RISK_ANALYSIS
            )
        """
        combined = []
        for toolset in toolsets:
            for tool in toolset:
                if tool not in combined:
                    combined.append(tool)
        return combined
    
    @staticmethod
    def extend(base_toolset: List[str], additional_tools: List[str]) -> List[str]:
        """
        Расширяет базовый набор инструментов дополнительными.
        
        :param base_toolset: Базовый набор инструментов
        :param additional_tools: Дополнительные инструменты
        :return: Расширенный список без дубликатов
        
        Пример:
            tools = CommonToolSets.extend(
                CommonToolSets.BASIC_SEARCH,
                ["priority_filter", "custom_validator"]
            )
        """
        return CommonToolSets.combine(base_toolset, additional_tools)
    
    @staticmethod
    def get_available_toolsets() -> dict:
        """
        Возвращает словарь всех доступных наборов инструментов.
        Полезно для документации и отладки.
        """
        return {
            "BASIC_SEARCH": CommonToolSets.BASIC_SEARCH,
            "RISK_ANALYSIS": CommonToolSets.RISK_ANALYSIS,
            "CONTRACTOR_ANALYSIS": CommonToolSets.CONTRACTOR_ANALYSIS,
            "ERROR_ANALYSIS": CommonToolSets.ERROR_ANALYSIS,
            "PROCESS_ANALYSIS": CommonToolSets.PROCESS_ANALYSIS,
            "FULL_ANALYSIS": CommonToolSets.FULL_ANALYSIS,
            "MINIMAL": CommonToolSets.MINIMAL
        }


# Для удобства импорта можно создать алиасы
ToolSets = CommonToolSets  # Короткий алиас