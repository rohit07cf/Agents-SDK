"""
agent_node.py - Single node in the agent hierarchy.

Same shape as configurable_agent/agent_tree.py AgentNode:
  - name, agent reference, children list, tools list

Kept as a thin wrapper so we can extend without touching
the original configurable_agent code.
"""

from __future__ import annotations

from typing import Any, List, Optional


class AgentNode:
    """
    One node in an agent tree.

    Attributes:
        name:     human-readable agent name
        agent:    reference to the actual Agent object (or None)
        children: child AgentNodes
        tools:    tool names available to this agent
        role:     short description (e.g. "supervisor", "specialist")
    """

    def __init__(
        self,
        name: str,
        agent: Optional[Any] = None,
        role: str = "",
    ):
        self.name = name
        self.agent = agent
        self.role = role
        self.children: List[AgentNode] = []
        self.tools: List[str] = []

    def add_child(self, child: AgentNode) -> AgentNode:
        """Attach a child node and return it for chaining."""
        self.children.append(child)
        return child

    def add_tool(self, tool_name: str) -> None:
        """Register a tool name for this node."""
        self.tools.append(tool_name)

    def __repr__(self) -> str:
        return (
            f"AgentNode(name={self.name!r}, role={self.role!r}, "
            f"children={len(self.children)}, tools={self.tools})"
        )
