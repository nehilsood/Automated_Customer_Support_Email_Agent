"""Base tool class and registry for agent tools."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    """Result from tool execution."""

    success: bool
    data: Any = None
    error: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {"success": self.success}
        if self.data is not None:
            result["data"] = self.data
        if self.error:
            result["error"] = self.error
        return result


class BaseTool(ABC):
    """Base class for all agent tools."""

    name: str
    description: str
    parameters: dict[str, Any]

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters.

        Args:
            **kwargs: Tool-specific parameters.

        Returns:
            ToolResult with success status and data or error.
        """
        pass

    def get_openai_function_schema(self) -> dict:
        """Get OpenAI function calling schema for this tool.

        Returns:
            Dictionary in OpenAI function format.
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


@dataclass
class ToolRegistry:
    """Registry for managing available tools."""

    _tools: dict[str, BaseTool] = field(default_factory=dict)

    def register(self, tool: BaseTool) -> None:
        """Register a tool in the registry.

        Args:
            tool: Tool instance to register.
        """
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        """Get a tool by name.

        Args:
            name: Tool name.

        Returns:
            Tool instance or None if not found.
        """
        return self._tools.get(name)

    def get_all(self) -> list[BaseTool]:
        """Get all registered tools.

        Returns:
            List of all tool instances.
        """
        return list(self._tools.values())

    def get_openai_tools_schema(self) -> list[dict]:
        """Get OpenAI tools schema for all registered tools.

        Returns:
            List of tool schemas in OpenAI format.
        """
        return [tool.get_openai_function_schema() for tool in self._tools.values()]

    async def execute(self, name: str, **kwargs) -> ToolResult:
        """Execute a tool by name.

        Args:
            name: Tool name.
            **kwargs: Tool parameters.

        Returns:
            ToolResult from tool execution.
        """
        tool = self.get(name)
        if not tool:
            return ToolResult(success=False, error=f"Tool '{name}' not found")
        return await tool.execute(**kwargs)
