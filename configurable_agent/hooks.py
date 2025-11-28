# hooks.py
from typing import Any

from agents import Agent
from agents.lifecycle import AgentHooks as BaseAgentHooks, RunHooks as BaseRunHooks, RunContextWrapper


class MyAgentHooks(BaseAgentHooks):
    """
    Per-agent lifecycle hooks from the OpenAI Agents SDK.
    Attach to a specific Agent via the `hooks` argument.
    """

    async def on_start(
        self,
        context: RunContextWrapper,
        agent: Agent,
    ) -> None:
        print(f"🔵 [AgentHooks:on_start] {agent.name}")

    async def on_end(
        self,
        context: RunContextWrapper,
        agent: Agent,
        output: Any,
    ) -> None:
        print(f"🟢 [AgentHooks:on_end] {agent.name} → {output}")

    async def on_handoff(
        self,
        context: RunContextWrapper,
        agent: Agent,
        source: Agent,
    ) -> None:
        print(f"🤝 [AgentHooks:on_handoff] {source.name} → {agent.name}")


class MyRunHooks(BaseRunHooks):
    """
    Global run-level hooks.
    Pass an instance to Runner.run(..., hooks=MyRunHooks()).
    """

    async def on_agent_start(
        self,
        context: RunContextWrapper,
        agent: Agent,
    ) -> None:
        print(f"🟣 [RunHooks:on_agent_start] {agent.name}")

    async def on_agent_end(
        self,
        context: RunContextWrapper,
        agent: Agent,
        output: Any,
    ) -> None:
        print(f"🟣 [RunHooks:on_agent_end] {agent.name} → {output}")

    async def on_tool_start(
        self,
        context: RunContextWrapper,
        agent: Agent,
        tool,
    ) -> None:
        print(f"⚙️ [RunHooks:on_tool_start] {tool.name} (agent={agent.name})")

    async def on_tool_end(
        self,
        context: RunContextWrapper,
        agent: Agent,
        tool,
        result: Any,
    ) -> None:
        print(f"⚙️ [RunHooks:on_tool_end] {tool.name} → {result}")


# 🔥 NEW: Reasoning hook for ReAct "REASON" steps
class ReasoningHooks:
    """
    Custom hook for logging 'REASON' steps in a ReAct pattern.
    Called explicitly by the reasoning_step tool.
    """

    async def on_reasoning_step(self, thought: str) -> None:
        # You can swap this print for more advanced logging later
        print(f"🧠 [REASON-STEP] {thought}")


# Global instance that tools can import/use
reasoning_hooks = ReasoningHooks()
