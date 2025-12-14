# activities.py
import json
from typing import Any, Dict, List

from temporalio import activity

from agents import Runner
from hooks import MyRunHooks
from models import SupervisorOutput
from reasoner import call_reasoner
from sdk_agents import supervisor_agent
from agent_tree import AgentNode, AgentTree
from sdk_agents import simple_agent, math_agent, echo_agent, classifier_agent


def build_agents_and_tools_map() -> Dict[str, List[str]]:
    return {
        "Supervisor": ["reasoning_step"],  # conceptually
        "SimpleAgent": ["add_numbers", "echo_text"],
        "MathAgent": ["add_numbers", "subtract_numbers", "multiply_numbers"],
        "EchoAgent": ["echo_text", "reverse_text"],
        "ClassifierAgent": ["classify_intent", "detect_sentiment"],
    }


def build_agent_tree() -> AgentTree:
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

    return AgentTree(root=supervisor_node)


@activity.defn
async def planner_activity(user_message: str) -> Dict[str, Any]:
    """
    Activity that calls your LLM planner (call_reasoner) to produce a plan JSON.
    This is where external OpenAI call happens (allowed in activities).
    """
    agents_and_tools = build_agents_and_tools_map()
    previous_tool_calls: List[Dict[str, Any]] = []

    plan = await call_reasoner(
        current_agent="Supervisor",
        agents_and_tools=agents_and_tools,
        previous_tool_calls=previous_tool_calls,
        input_message=user_message,
    )

    return plan


@activity.defn
async def orchestrator_activity(
    user_message: str,
    plan: Dict[str, Any],
) -> SupervisorOutput:
    """
    Activity that runs the OpenAI Agents SDK pipeline (Supervisor + children).
    Returns your structured SupervisorOutput.
    """
    # Build tree (optional, for logging/graph viz)
    tree = build_agent_tree()
    # You can print or log this; leaving it simple here.
    tree.visualize_console()

    execution_input = (
        "SYSTEM PLAN (from planner):\n"
        + json.dumps(plan, indent=2)
        + "\n\nUSER QUERY:\n"
        + user_message
    )

    result = await Runner.run(
        starting_agent=supervisor_agent,
        input=execution_input,
        hooks=MyRunHooks(),
    )

    # result.final_output is already SupervisorOutput because of output_type on supervisor_agent
    supervisor_output: SupervisorOutput = result.final_output
    return supervisor_output
