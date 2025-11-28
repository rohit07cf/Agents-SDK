# main.py
import asyncio
import json

from agents import Runner

from agent_tree import AgentNode, AgentTree
from models import SupervisorOutput
from hooks import MyRunHooks
from sdk_agents import (
    supervisor_agent,
    simple_agent,
    math_agent,
    echo_agent,
    classifier_agent,
)
from reasoner import call_reasoner


def build_agents_and_tools_map():
    """Describe tools per agent for the planner."""
    return {
        "Supervisor": ["transfer_to_supervisor", "reasoning_step"],  # conceptually
        "SimpleAgent": ["add_numbers", "echo_text"],
        "MathAgent": ["add_numbers", "subtract_numbers", "multiply_numbers"],
        "EchoAgent": ["echo_text", "reverse_text"],
        "ClassifierAgent": ["classify_intent", "detect_sentiment"],
    }


async def main():
    # ----- build visualization tree (unchanged) -----
    supervisor_node = AgentNode("Supervisor", agent=supervisor_agent)
    simple_node = supervisor_node.add_child(AgentNode("SimpleAgent", agent=simple_agent))
    math_node = supervisor_node.add_child(AgentNode("MathAgent", agent=math_agent))
    echo_node = supervisor_node.add_child(AgentNode("EchoAgent", agent=echo_agent))
    classifier_node = supervisor_node.add_child(
        AgentNode("ClassifierAgent", agent=classifier_agent)
    )

    simple_node.tools = ["add_numbers", "echo_text"]
    math_node.tools = ["add_numbers", "subtract_numbers", "multiply_numbers"]
    echo_node.tools = ["echo_text", "reverse_text"]
    classifier_node.tools = ["classify_intent", "detect_sentiment"]

    tree = AgentTree(root=supervisor_node)
    tree.visualize()

    # ----- user query -----
    user_message = "Whats the sentiments for: 'I am disappointed with the service provided'. Reverse the string '!EMOSEWA SI TIHOR'. Also multiply 2 and 3."

    # ----- 1) PLANNING / REASONING CALL -----
    agents_and_tools = build_agents_and_tools_map()
    previous_tool_calls = []  # later you can record & feed this back

    plan = await call_reasoner(
        current_agent="Supervisor",
        agents_and_tools=agents_and_tools,
        previous_tool_calls=previous_tool_calls,
        input_message=user_message,
    )

    print("\n🧠 PLANNER OUTPUT (REASONING PLAN):")
    print(json.dumps(plan, indent=2))

    # Simple example: tuck the plan + user query together
    execution_input = (
        "SYSTEM PLAN (from planner):\n"
        + json.dumps(plan, indent=2)
        + "\n\nUSER QUERY:\n"
        + user_message
    )

    # ----- 2) EXECUTION VIA SUPERVISOR + CHILD AGENTS -----
    result = await Runner.run(
        starting_agent=supervisor_agent,
        input=execution_input,
        hooks=MyRunHooks(),
    )

    print("\n🏁 FINAL OUTPUT FROM PIPELINE:")
    print(result.final_output)
    print("======================================================================================")
    print(SupervisorOutput.model_validate_json(result.final_output.model_dump_json(indent=2)))


if __name__ == "__main__":
    asyncio.run(main())
