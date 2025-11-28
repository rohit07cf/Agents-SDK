# main.py
import asyncio
import json

import streamlit as st

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
        "Supervisor": ["reasoning_step"],  # conceptually, since we changed to manager pattern
        "SimpleAgent": ["add_numbers", "echo_text"],
        "MathAgent": ["add_numbers", "subtract_numbers", "multiply_numbers"],
        "EchoAgent": ["echo_text", "reverse_text"],
        "ClassifierAgent": ["classify_intent", "detect_sentiment"],
    }


def build_agent_tree() -> AgentTree:
    """Build the static agent tree structure."""
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


async def run_pipeline(user_message: str):
    """
    End-to-end pipeline:
    1) Build tree
    2) Planner / reasoner call
    3) Supervisor + child agents via Runner.run
    Returns: (tree, plan, SupervisorOutput)
    """
    tree = build_agent_tree()

    # 1) PLANNING / REASONING CALL
    agents_and_tools = build_agents_and_tools_map()
    previous_tool_calls = []  # later you can record & feed this back

    plan = await call_reasoner(
        current_agent="Supervisor",
        agents_and_tools=agents_and_tools,
        previous_tool_calls=previous_tool_calls,
        input_message=user_message,
    )

    # 2) EXECUTION VIA SUPERVISOR + CHILD AGENTS
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

    # result.final_output is already a SupervisorOutput because of output_type
    supervisor_output: SupervisorOutput = result.final_output

    return tree, plan, supervisor_output


def main():
    st.set_page_config(page_title="Agentic Supervisor Orchestrator", layout="wide")
    st.title("🧠 Agentic Supervisor Orchestrator Demo")

    st.markdown(
        """
This app runs a **planner → supervisor → child agent** pipeline using the OpenAI Agents SDK.

1. A **planner LLM** creates a structured plan for the next step.
2. A **Supervisor agent** orchestrates specialized child agents:
   - SimpleAgent
   - MathAgent
   - EchoAgent
   - ClassifierAgent
3. The Supervisor returns a structured `SupervisorOutput` object.
"""
    )

    # --- Left column: input + controls ---
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("User Query")
        default_msg = (
            "Whats the sentiments for: 'I am disappointed with the service provided'. "
            "Reverse the string '!EMOSEWA SI TIHOR'. Also multiply 2 and 3."
        )
        user_message = st.text_area("Enter a query:", value=default_msg, height=160)

        run_button = st.button("Run Pipeline", type="primary")

    # --- Right column: agent tree viz ---
    with col2:
        st.subheader("Agent Tree")
        tree = build_agent_tree()
        # If your AgentTree.visualize() returns a Digraph, use that:
        try:
            dot = tree.visualize() #to_digraph()  # or tree.visualize() if you defined it that way
            st.graphviz_chart(dot.source)
        except Exception:
            # Fallback: console-style text
            st.text("Tree visualization unavailable; showing text view:")
            # simple textual view
            import io, contextlib

            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                tree.visualize_console()
            st.text(buf.getvalue())

    if run_button:
        if not user_message.strip():
            st.warning("Please enter a user query first.")
            return

        with st.spinner("Running planner + supervisor + child agents..."):
            tree, plan, supervisor_output = asyncio.run(run_pipeline(user_message))

        st.success("Run complete!")

        # --- Planner output ---
        st.subheader("🧠 Planner Output (Reasoning Plan)")
        st.json(plan)

        # --- Final structured output ---
        st.subheader("🏁 Final Structured Output (SupervisorOutput)")
        st.markdown("**Final Answer:**")
        st.write(supervisor_output.final_answer)

        st.markdown("**Subtask Breakdown:**")
        if supervisor_output.subtasks:
            # Show as table
            subtasks_data = [
                {
                    "Agent": st_res.agent,
                    "Subtask": st_res.subtask,
                    "Result": st_res.result,
                }
                for st_res in supervisor_output.subtasks
            ]
            st.table(subtasks_data)
        else:
            st.write("_No subtasks recorded in output._")

        # Optional: raw JSON view
        with st.expander("Raw JSON output"):
            st.code(supervisor_output.model_dump_json(indent=2), language="json")


if __name__ == "__main__":
    main()
