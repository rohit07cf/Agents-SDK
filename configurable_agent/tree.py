# tree.py
import re
from typing import Any

from tools import TOOLS
from hooks import AgentHooks, ToolHooks
from callbacks import StreamingCallback

# OpenAI Agents SDK
from agents import Agent as OAAgent, Runner


class BaseAgent:
    """
    Small shared base so all your agents behave similarly
    (hooks + tools + streaming + LLM-backed reasoning).
    """

    def __init__(self, name: str, instructions: str):
        self.name = name
        self.agent_hooks = AgentHooks()
        self.tool_hooks = ToolHooks()
        self.stream = StreamingCallback()

        # LLM-backed reasoning agent
        self.llm_agent = OAAgent(
            name=f"{name}-LLM",
            instructions=instructions,
        )

    async def _llm_reason(self, text: str) -> str:
        """
        Use OpenAI Agents SDK to get real reasoning from an LLM.
        This is where Runner.run is used.
        """
        # Stream that we're "thinking"
        self.stream.on_step("🔍 Calling LLM for reasoning...\n")

        result = await Runner.run(
            starting_agent=self.llm_agent,
            input=f"Think step-by-step about how to respond to this user input. "
                  f"Keep it short (~2-3 sentences).\nUser: {text}",
        )
        reasoning = str(result.final_output)
        self.stream.on_step(reasoning + "\n")
        return reasoning

    async def _use_tool(self, name: str, args: dict) -> Any:
        await self.tool_hooks.on_tool_start(name, args)
        fn = TOOLS[name]
        result = fn(**args)
        await self.tool_hooks.on_tool_end(name, result)
        return result


class SimpleAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="SimpleAgent",
            instructions="You are a tiny reasoning module that decides whether "
                         "to just echo the text or to add numbers using tools."
        )

    async def run(self, user_input: str) -> str:
        await self.agent_hooks.on_agent_start(self.name, user_input)

        reasoning = await self._llm_reason(user_input)
        await self.agent_hooks.on_agent_step(self.name, reasoning)

        if "add" in user_input.lower():
            result = await self._use_tool("add_numbers", {"a": 5, "b": 7})
            step_msg = f"Tool result → {result}"
            await self.agent_hooks.on_agent_step(self.name, step_msg)
            final_output = f"Computed result: {result}"
        else:
            result = await self._use_tool("echo_text", {"text": user_input})
            final_output = result

        await self.agent_hooks.on_agent_end(self.name, final_output)
        self.stream.on_final(final_output)
        return final_output


class MathAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="MathAgent",
            instructions="You help with math queries and choose between add, subtract, "
                         "and multiply. You will also sometimes delegate simple integer "
                         "operations to local Python tools."
        )

    async def run(self, user_input: str) -> str:
        await self.agent_hooks.on_agent_start(self.name, user_input)

        reasoning = await self._llm_reason(user_input)
        await self.agent_hooks.on_agent_step(self.name, reasoning)

        # Extract first two integers from the text, default to (5, 7)
        nums = [int(x) for x in re.findall(r"-?\d+", user_input)]
        a, b = (nums[0], nums[1]) if len(nums) >= 2 else (5, 7)

        lowered = user_input.lower()
        if "subtract" in lowered or "minus" in lowered:
            op = "subtract_numbers"
            desc = "subtraction"
        elif "multiply" in lowered or "times" in lowered:
            op = "multiply_numbers"
            desc = "multiplication"
        else:
            op = "add_numbers"
            desc = "addition"

        step_msg = f"Chose {desc} on a={a}, b={b} via tool {op}"
        await self.agent_hooks.on_agent_step(self.name, step_msg)

        result = await self._use_tool(op, {"a": a, "b": b})
        final_output = f"{desc.capitalize()} result for {a} and {b}: {result}"

        await self.agent_hooks.on_agent_end(self.name, final_output)
        self.stream.on_final(final_output)
        return final_output


class EchoAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="EchoAgent",
            instructions="You are an echo-style agent. Decide whether to echo the text "
                         "normally or reverse it for fun."
        )

    async def run(self, user_input: str) -> str:
        await self.agent_hooks.on_agent_start(self.name, user_input)

        reasoning = await self._llm_reason(user_input)
        await self.agent_hooks.on_agent_step(self.name, reasoning)

        lowered = user_input.lower()
        if "reverse" in lowered or "backwards" in lowered:
            tool_name = "reverse_text"
        else:
            tool_name = "echo_text"

        result = await self._use_tool(tool_name, {"text": user_input})
        final_output = result

        await self.agent_hooks.on_agent_end(self.name, final_output)
        self.stream.on_final(final_output)
        return final_output


class ClassifierAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="ClassifierAgent",
            instructions=(
                "You classify user messages into intent and sentiment. "
                "You have access to local heuristic tools but can also reason yourself."
            )
        )

    async def run(self, user_input: str) -> str:
        await self.agent_hooks.on_agent_start(self.name, user_input)

        reasoning = await self._llm_reason(user_input)
        await self.agent_hooks.on_agent_step(self.name, reasoning)

        intent = await self._use_tool("classify_intent", {"text": user_input})
        sentiment = await self._use_tool("detect_sentiment", {"text": user_input})

        final_output = (
            f"Intent: {intent}\n"
            f"Sentiment: {sentiment}\n"
            f"LLM reasoning: {reasoning}"
        )

        await self.agent_hooks.on_agent_end(self.name, final_output)
        self.stream.on_final(final_output)
        return final_output
