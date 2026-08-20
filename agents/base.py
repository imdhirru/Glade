"""Base agent class and interfaces for Glade AI agent system."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class AgentContext:
    """Context passed to agents for decision making."""
    user_id: str
    goal: Optional[str] = None
    workflow_id: Optional[str] = None
    current_stage: Optional[int] = None
    completed_wins: Optional[List[str]] = None
    available_tools: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AgentResult:
    """Result returned by agent execution."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    reasoning: Optional[str] = None
    next_agent: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class Tool:
    """Base tool interface that agents can use."""

    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        status: str = "preview"
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.status = status  # "preview" or "ready"

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with given parameters."""
        raise NotImplementedError(f"Tool {self.name} must implement execute()")

    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary for API responses."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "status": self.status
        }


class ToolRegistry:
    """Registry for managing available tools."""

    def __init__(self):
        self.tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool."""
        self.tools[tool.name] = tool
        logger.info(f"Tool registered: {tool.name} ({tool.status})")

    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self.tools.get(name)

    def get_available_tools(self) -> List[Tool]:
        """Get all tools that are ready (connected to real APIs)."""
        return [t for t in self.tools.values() if t.status == "ready"]

    def get_preview_tools(self) -> List[Tool]:
        """Get all tools that are in preview mode."""
        return [t for t in self.tools.values() if t.status == "preview"]

    def get_all_tools(self) -> List[Tool]:
        """Get all tools."""
        return list(self.tools.values())

    def mark_tool_ready(self, name: str) -> bool:
        """Mark a tool as ready (connected to API)."""
        tool = self.get_tool(name)
        if tool:
            tool.status = "ready"
            logger.info(f"Tool marked as ready: {name}")
            return True
        return False

    def to_dict(self) -> Dict[str, List[Dict[str, Any]]]:
        """Convert registry to dictionary."""
        return {
            "available": [t.to_dict() for t in self.get_available_tools()],
            "preview": [t.to_dict() for t in self.get_preview_tools()]
        }


class Agent(ABC):
    """Base agent class that all agents inherit from."""

    def __init__(
        self,
        name: str,
        description: str,
        tool_registry: Optional[ToolRegistry] = None
    ):
        self.name = name
        self.description = description
        self.tool_registry = tool_registry or ToolRegistry()
        self.logger = logging.getLogger(f"glade.agent.{name.lower()}")

    @abstractmethod
    async def execute(
        self,
        context: AgentContext,
        prompt: str
    ) -> AgentResult:
        """Execute the agent with given context and prompt."""
        pass

    async def think(self, situation: str) -> str:
        """Agent reasoning step."""
        self.logger.info(f"Thinking about: {situation}")
        return "Analysis complete"

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools for this agent."""
        return [t.to_dict() for t in self.tool_registry.get_available_tools()]

    def log_execution(
        self,
        status: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log agent execution details."""
        self.logger.info(f"[{self.name}] {status}")
        if details:
            self.logger.debug(f"Details: {details}")

    def create_result(
        self,
        success: bool,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        reasoning: Optional[str] = None,
        next_agent: Optional[str] = None
    ) -> AgentResult:
        """Create a result object for this agent."""
        result = AgentResult(
            success=success,
            data=data,
            error=error,
            reasoning=reasoning,
            next_agent=next_agent
        )

        if success:
            self.log_execution("Success", data)
        else:
            self.logger.error(f"Execution failed: {error}")

        return result
