"""
configurable_agent_factory.py - Build Agent instances from Pydantic configs.

Pattern taken from configurable_agent/sdk_agents.py:
  - Each agent is created with (name, instructions, tools, model)
  - Supervisor wires child agents via .as_tool() or handoff()

This factory centralizes that logic so configs are the single source of truth.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, List, Optional, Type

from pydantic import BaseModel

from schemas import AgentConfig, HandoffResult, ToolResponse, TreeConfig


# ── Thin Agent Wrapper ──────────────────────────────────────────────
# Mirrors the openai-agents SDK Agent interface but runs locally
# so examples are self-contained (no API key required).
# In production, swap this with `from agents import Agent`.


class Agent:
    """
    Minimal agent that:
      - accepts an input string
      - optionally calls tools
      - returns validated structured output
    """

    def __init__(
        self,
        name: str,
        instructions: str,
        model: str = "gpt-4.1-mini",
        tools: Optional[List[Callable]] = None,
        output_type: Optional[Type[BaseModel]] = None,
    ):
        self.name = name
        self.instructions = instructions
        self.model = model
        self.tools: List[Callable] = tools or []
        self.output_type = output_type
        self._tool_map: Dict[str, Callable] = {
            t.__name__ if hasattr(t, "__name__") else str(t): t
            for t in self.tools
        }

    # ── core execution ──────────────────────────────────────────────

    async def run(self, input_text: str, **kwargs) -> Any:
        """
        Execute the agent's logic.

        In a real SDK integration this calls Runner.run().
        Here we simulate: run each tool, collect results,
        and return a validated Pydantic output if output_type is set.
        """
        results = {}
        for tool_name, tool_fn in self._tool_map.items():
            # Call each tool with the input
            if asyncio.iscoroutinefunction(tool_fn):
                result = await tool_fn(input_text)
            else:
                result = tool_fn(input_text)
            results[tool_name] = result

        # Build structured output if requested
        if self.output_type and kwargs.get("output_data"):
            return self.output_type(**kwargs["output_data"])

        return results

    # ── agent-as-tool adapter ───────────────────────────────────────

    def as_tool(self, tool_name: str, tool_description: str = "") -> Callable:
        """
        Wrap this agent as a callable tool function.

        Same pattern as openai-agents SDK:
          child_agent.as_tool(tool_name="run_child", ...)

        The parent agent stays in control; child runs as a bounded call.
        """
        agent_ref = self

        async def _tool_fn(input_text: str) -> str:
            result = await agent_ref.run(input_text)
            return str(result)

        _tool_fn.__name__ = tool_name
        _tool_fn.__doc__ = tool_description
        return _tool_fn

    def __repr__(self) -> str:
        return f"Agent(name={self.name!r}, tools={list(self._tool_map.keys())})"


# ── Tool Registry ──────────────────────────────────────────────────
# Maps tool name strings (from AgentConfig.tools) to actual callables.

_TOOL_REGISTRY: Dict[str, Callable] = {}


def register_tool(name: str, fn: Callable) -> None:
    """Register a callable so the factory can look it up by name."""
    _TOOL_REGISTRY[name] = fn


def get_tool(name: str) -> Callable:
    """Retrieve a registered tool by name."""
    if name not in _TOOL_REGISTRY:
        raise KeyError(f"Tool '{name}' not registered. Available: {list(_TOOL_REGISTRY.keys())}")
    return _TOOL_REGISTRY[name]


# ── Factory Function ───────────────────────────────────────────────


def create_agent_from_config(agent_config: AgentConfig) -> Agent:
    """
    Build an Agent instance from a Pydantic AgentConfig.

    Steps:
      1. Resolve tool names -> callables via registry
      2. Build system prompt from PromptConfig
      3. Instantiate Agent with config values

    This mirrors configurable_agent/sdk_agents.py but is config-driven.
    """
    # Resolve tools
    resolved_tools = []
    for tool_name in agent_config.tools:
        try:
            resolved_tools.append(get_tool(tool_name))
        except KeyError:
            # Tool not registered yet - skip with warning
            print(f"  [warn] Tool '{tool_name}' not in registry, skipping")

    return Agent(
        name=agent_config.name,
        instructions=agent_config.prompt_config.system_template,
        model=agent_config.model_config_.model_name,
        tools=resolved_tools,
    )


def build_agents_from_tree_config(tree_config: TreeConfig) -> Dict[str, Agent]:
    """
    Build all agents (supervisor + children) from a TreeConfig.

    Returns a dict: { agent_name: Agent }
    """
    agents: Dict[str, Agent] = {}

    # Build children first
    for child_cfg in tree_config.children:
        agents[child_cfg.name] = create_agent_from_config(child_cfg)

    # Build supervisor
    agents[tree_config.supervisor.name] = create_agent_from_config(tree_config.supervisor)

    return agents
