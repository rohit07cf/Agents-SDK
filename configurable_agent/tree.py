# tree.py
from typing import Any
from tools import TOOLS
from hooks import AgentHooks, ToolHooks
from callbacks import StreamingCallback
#from openai import AsyncClient

#client = AsyncClient()

class SimpleAgent:
    def __init__(self):
        self.agent_hooks = AgentHooks()
        self.tool_hooks = ToolHooks()
        self.stream = StreamingCallback()

    async def run(self, user_input: str) -> str:
        await self.agent_hooks.on_agent_start("SimpleAgent", user_input)

        # Step 1: Decide what to do (LLM reasoning)
        reasoning = await self._llm_reason(user_input)
        await self.agent_hooks.on_agent_step("SimpleAgent", reasoning)

        # Step 2: If a tool is needed, call it
        if "add" in user_input:
            result = await self._use_tool("add_numbers", {"a": 5, "b": 7})
            await self.agent_hooks.on_agent_step("SimpleAgent", f"Tool result → {result}")
            final_output = f"Computed result: {result}"

        else:
            final_output = f"Echo: {user_input}"

        await self.agent_hooks.on_agent_end("SimpleAgent", final_output)
        self.stream.on_final(final_output)
        return final_output

    async def _llm_reason(self, text: str) -> str:
        """Simulate streaming reasoning."""
        fake_steps = [
            "Thinking...", 
            "Determining intent...", 
            "Checking if tools required..."
        ]
        for step in fake_steps:
            self.stream.on_step(step + "\n")
        return "Reasoning complete"

    async def _use_tool(self, name: str, args: dict) -> Any:
        await self.tool_hooks.on_tool_start(name, args)
        fn = TOOLS[name]
        result = fn(**args)
        await self.tool_hooks.on_tool_end(name, result)
        return result
