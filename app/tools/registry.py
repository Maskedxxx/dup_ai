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


# Создаем единый экземпляр реестра для всего приложения
tool_registry = ToolRegistry()
