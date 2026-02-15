"""
agent_tree - Hierarchical agent structure.

Reuses the AgentNode / AgentTree pattern from
configurable_agent/agent_tree.py with added ASCII visualization
and config-driven tree construction.
"""

from .agent_node import AgentNode
from .agent_tree import AgentTree

__all__ = ["AgentNode", "AgentTree"]
