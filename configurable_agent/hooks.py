# hooks.py
import time

class AgentHooks:
    async def on_agent_start(self, agent_name: str, user_input: str):
        print(f"🔵 [AGENT-START] {agent_name} → {user_input}")

    async def on_agent_step(self, agent_name: str, step_info: str):
        print(f"🟡 [AGENT-STEP] {agent_name} → {step_info}")

    async def on_agent_end(self, agent_name: str, output: str):
        print(f"🟢 [AGENT-END] {agent_name} → {output}")


class ToolHooks:
    async def on_tool_start(self, tool_name: str, args: dict):
        print(f"⚙️  [TOOL-START] {tool_name} args={args}")

    async def on_tool_end(self, tool_name: str, result: any):
        print(f"⚙️  [TOOL-END] {tool_name} result={result}")
