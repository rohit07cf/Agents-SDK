"""
configurable_agent_factory.py - Build agents with HITL integration.

Mirrors configurable_agent/sdk_agents.py + handoffs factory pattern:
  - Agents created from AgentConfig (Pydantic)
  - Tool registry maps names -> callables
  - HITL policy check wraps every tool call

Key addition vs the base factory:
  - execute_tool_with_hitl() checks policy BEFORE running any tool
  - If approval required -> calls request_human_approval tool
  - If denied -> stops execution, returns denial
  - If approved with edits -> applies edited args, then executes
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Type

from pydantic import BaseModel

from schemas import (
    AgentConfig,
    ApprovalDecision,
    ApprovalRequest,
    HITLConfig,
)
from hitl_policy import HITLPolicy
from hitl_tool import request_human_approval
from approval_store import InMemoryApprovalStore


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Thin Agent Wrapper (same pattern as handoffs_vs_agents_as_tools/)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class Agent:
    """
    Minimal agent that mirrors the OpenAI Agents SDK Agent.

    In production, replace with: from agents import Agent
    This wrapper lets examples run without an API key.
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

    async def run(self, input_text: str, **kwargs) -> Any:
        results = {}
        for tool_name, tool_fn in self._tool_map.items():
            if asyncio.iscoroutinefunction(tool_fn):
                result = await tool_fn(input_text)
            else:
                result = tool_fn(input_text)
            results[tool_name] = result

        if self.output_type and kwargs.get("output_data"):
            return self.output_type(**kwargs["output_data"])
        return results

    def __repr__(self) -> str:
        return f"Agent(name={self.name!r}, tools={list(self._tool_map.keys())})"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Tool Registry
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_TOOL_REGISTRY: Dict[str, Callable] = {}


def register_tool(name: str, fn: Callable) -> None:
    """Register a tool callable by name."""
    _TOOL_REGISTRY[name] = fn


def get_tool(name: str) -> Callable:
    """Look up a registered tool."""
    if name not in _TOOL_REGISTRY:
        raise KeyError(f"Tool '{name}' not registered. Available: {list(_TOOL_REGISTRY.keys())}")
    return _TOOL_REGISTRY[name]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Factory: Agent from Config
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def create_agent_from_config(agent_config: AgentConfig) -> Agent:
    """
    Build an Agent from a Pydantic AgentConfig.

    Same pattern as configurable_agent/sdk_agents.py:
      1. Resolve tool names -> callables
      2. Build instructions from PromptConfig
      3. Instantiate Agent
    """
    resolved_tools = []
    for tool_name in agent_config.tools:
        try:
            resolved_tools.append(get_tool(tool_name))
        except KeyError:
            print(f"  [warn] Tool '{tool_name}' not in registry, skipping")

    return Agent(
        name=agent_config.name,
        instructions=agent_config.prompt_config.system_template,
        model=agent_config.model_config_.model_name,
        tools=resolved_tools,
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HITL-Wrapped Tool Execution (the key integration)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def execute_tool_with_hitl(
    agent_name: str,
    tool_name: str,
    tool_args: Dict[str, Any],
    hitl_config: HITLConfig,
    store: Optional[InMemoryApprovalStore] = None,
    input_fn: Optional[Callable] = None,
) -> Dict[str, Any]:
    """
    Execute a tool with HITL policy check.

    This is the wrapper that sits between the agent and every tool call:

      1. Consult HITL policy -> does this tool need approval?
      2. If yes  -> call request_human_approval tool
      3. If denied -> return denial, agent must adjust
      4. If approved with edited args -> use edited args
      5. Execute the actual tool
      6. Log what happened

    Returns:
        {
            "tool_name": str,
            "result": any,            # tool output (or None if denied)
            "hitl_decision": dict,     # approval decision (or None)
            "executed": bool,          # whether the tool actually ran
        }
    """
    store = store or InMemoryApprovalStore()
    policy = HITLPolicy(hitl_config)

    # Step 1: Check policy
    verdict = policy.evaluate(tool_name, tool_args)
    print(f"  [HITL] Policy check for '{tool_name}': {verdict}")

    if not verdict.needs_approval:
        # No approval needed -> execute directly
        result = _execute_tool(tool_name, tool_args)
        print(f"  [HITL] Executed '{tool_name}' directly (no approval needed)")
        return {
            "tool_name": tool_name,
            "result": result,
            "hitl_decision": None,
            "executed": True,
        }

    # Step 2: Approval required -> build request
    request = ApprovalRequest(
        request_id=str(uuid.uuid4())[:8],
        agent_name=agent_name,
        tool_name=tool_name,
        tool_args=tool_args,
        risk_level=verdict.risk_level,
        reason=verdict.reason,
    )

    # Step 3: Call the HITL tool
    decision = request_human_approval(
        request=request,
        config=hitl_config,
        store=store,
        input_fn=input_fn,
    )

    print(f"  [HITL] Decision: {decision.status} (comment: {decision.human_comment})")

    # Step 4: Handle decision
    if decision.status != "approved":
        print(f"  [HITL] Tool '{tool_name}' NOT executed ({decision.status})")
        return {
            "tool_name": tool_name,
            "result": None,
            "hitl_decision": decision.model_dump(),
            "executed": False,
        }

    # Step 5: Apply edited args if human modified them
    final_args = decision.edited_tool_args if decision.edited_tool_args else tool_args
    if decision.edited_tool_args:
        print(f"  [HITL] Using edited args: {final_args}")

    # Step 6: Execute
    result = _execute_tool(tool_name, final_args)
    print(f"  [HITL] Executed '{tool_name}' after approval")

    return {
        "tool_name": tool_name,
        "result": result,
        "hitl_decision": decision.model_dump(),
        "executed": True,
    }


def _execute_tool(tool_name: str, tool_args: Dict[str, Any]) -> Any:
    """Look up and call a registered tool with the given args."""
    tool_fn = get_tool(tool_name)
    return tool_fn(**tool_args)
