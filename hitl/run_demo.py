# run_demo.py (core pattern)
import json
from langgraph.types import Command
from graph_builder import build_graph

graph = build_graph()
THREAD_ID = "demo-thread-001"
config = {"configurable": {"thread_id": THREAD_ID}}

initial_state = {"messages": [{"role": "user", "content": "add 10 and 32"}]}

for event in graph.stream(initial_state, config=config):
    if "__interrupt__" in event:
        payload = event["__interrupt__"][0].value
        print("\nHITL REQUEST:")
        print(json.dumps(payload, indent=2))

        # Example: revise args
        human_input = {
            "request_id": payload["request_id"],
            "decision": "revise",
            "revised_args": {"a": 100, "b": 23},
            "note": "Use different numbers",
        }

        resumed = graph.invoke(
            Command(resume=human_input),   # <-- not {"human_input": human_input}
            config=config,
        )

        print("\nRESUMED RESULT:")
        print(json.dumps(resumed.get("last_tool_result"), indent=2))
        break
