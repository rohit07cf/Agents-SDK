"""
agent_tree.py - Tree of AgentNodes with ASCII visualization.

Same pattern as configurable_agent/agent_tree.py AgentTree but:
  - Pure ASCII visualize() (no graphviz dependency)
  - build_from_config() class method for config-driven construction
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional

from .agent_node import AgentNode

if TYPE_CHECKING:
    from schemas import TreeConfig


class AgentTree:
    """
    Hierarchical structure: supervisor (root) + child agents.

    Usage:
        tree = AgentTree(root=supervisor_node)
        tree.visualize()
    """

    def __init__(self, root: AgentNode):
        self.root = root

    # ── ASCII visualization ─────────────────────────────────────────

    def visualize(self) -> str:
        """Print and return an ASCII tree."""
        lines = ["Agent Tree Structure:", ""]
        self._render_node(self.root, lines, prefix="", is_last=True)
        output = "\n".join(lines)
        print(output)
        return output

    def _render_node(
        self,
        node: AgentNode,
        lines: list,
        prefix: str,
        is_last: bool,
    ) -> None:
        connector = "`-- " if is_last else "|-- "
        tools_str = f" [{', '.join(node.tools)}]" if node.tools else ""
        role_str = f" ({node.role})" if node.role else ""
        lines.append(f"{prefix}{connector}{node.name}{role_str}{tools_str}")

        child_prefix = prefix + ("    " if is_last else "|   ")
        for i, child in enumerate(node.children):
            self._render_node(
                child, lines, child_prefix, is_last=(i == len(node.children) - 1)
            )

    # ── config-driven builder ───────────────────────────────────────

    @classmethod
    def build_from_config(
        cls,
        tree_config: "TreeConfig",
        agents: Optional[Dict[str, object]] = None,
    ) -> "AgentTree":
        """
        Construct an AgentTree from a TreeConfig.

        Args:
            tree_config: Pydantic config with supervisor + children
            agents: optional dict of {name: Agent} to attach references
        """
        agents = agents or {}

        # Root node
        sup_cfg = tree_config.supervisor
        root = AgentNode(
            name=sup_cfg.name,
            agent=agents.get(sup_cfg.name),
            role=sup_cfg.role,
        )
        for t in sup_cfg.tools:
            root.add_tool(t)

        # Child nodes
        for child_cfg in tree_config.children:
            child_node = AgentNode(
                name=child_cfg.name,
                agent=agents.get(child_cfg.name),
                role=child_cfg.role,
            )
            for t in child_cfg.tools:
                child_node.add_tool(t)
            root.add_child(child_node)

        return cls(root=root)
