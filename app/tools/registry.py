# app/tools/registry.py

from typing import Dict, List, Any, Optional
from app.tools.base_tool import BaseTool
from app.tools.keyword_search_tool import KeywordSearchTool
from app.utils.logging import setup_logger

# Настройка логгера
logger = setup_logger(__name__)


class ToolRegistry:
    """
    Реестр для хранения и управления всеми доступными инструментами.
    """
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._register_tools()
    
    def _register_tools(self):
        """
        Регистрирует все доступные инструменты.
        Чтобы добавить новый инструмент, просто импортируйте его и добавьте в словарь.
        """
        keyword_search = KeywordSearchTool()
        self.register_tool(keyword_search)
        
    def register_tool(self, tool: BaseTool):
        """
        Регистрирует один экземпляр инструмента.
        Имя инструмента берется из его схемы.
        """
        schema = tool.get_schema()
        tool_name = schema.get("function", {}).get("name")
        
        if not tool_name:
            logger.error(f"Не удалось зарегистрировать инструмент: отсутствует имя в схеме {schema}")
            return
            
        if tool_name in self._tools:
            logger.warning(f"Инструмент с именем '{tool_name}' уже зарегистрирован. Перезапись.")
            
        self._tools[tool_name] = tool
        logger.info(f"Инструмент '{tool_name}' успешно зарегистрирован.")

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        Возвращает экземпляр инструмента по его имени.
        
        :param name: Имя инструмента.
        :return: Экземпляр BaseTool или None, если не найден.
        """
        return self._tools.get(name)

    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """
        Возвращает список JSON-схем всех зарегистрированных инструментов.
        
        :return: Список словарей со схемами.
        """
        return [tool.get_schema() for tool in self._tools.values()]

    def get_schemas_by_names(self, names: List[str]) -> List[Dict[str, Any]]:
        """
        Возвращает схемы только для инструментов с указанными именами.
        
        :param names: Список имен инструментов
        :return: Список схем для указанных инструментов
        
        Пример:
            registry = ToolRegistry()
            schemas = registry.get_schemas_by_names(["search_by_keywords", "filter_by_priority"])
        """
        if not names:
            logger.warning("Передан пустой список имен инструментов")
            return []
        
        schemas = []
        for name in names:
            tool = self._tools.get(name)
            if tool:
                schemas.append(tool.get_schema())
                logger.debug(f"Добавлена схема для инструмента '{name}'")
            else:
                logger.warning(f"Инструмент '{name}' не найден в реестре")
        
        logger.info(f"Возвращено {len(schemas)} схем из {len(names)} запрошенных")
        return schemas

    def get_available_tool_names(self) -> List[str]:
        """
        Возвращает список имен всех доступных инструментов.
        Полезно для отладки и документации.
        
        :return: Список имен зарегистрированных инструментов
        """
        return list(self._tools.keys())


# Создаем единый экземпляр реестра для всего приложения
tool_registry = ToolRegistry()
