import asyncio
from agents import Agent, Runner, gen_trace_id, trace
from agents.mcp import MCPServer, MCPServerSse
from agents.model_settings import ModelSettings

async def run(mcp_server: MCPServer):
    agent = Agent(
        name="Assistant",
        instructions="Use the tools to answer the questions.",
        mcp_servers=[mcp_server],
        model_settings=ModelSettings(tool_choice="required"),
    )

    while True:
        message = input("Ask something (or type 'exit' to quit): ")
        if message.lower() == "exit":
            break
        try:
            trace_id = gen_trace_id()
            with trace(workflow_name="MCP Tool Interaction", trace_id=trace_id):
                print(f"Trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
                result = await Runner.run(starting_agent=agent, input=message)
                print("Assistant Response:", result.final_output)
        except Exception as e:
            print("Error:", e)

async def main():
    async with MCPServerSse(
        name="SSE Python Server",
        params={
            "url": "http://localhost:8000/sse",
        },
    ) as server:
        await run(server)

if __name__ == "__main__":
    asyncio.run(main())
