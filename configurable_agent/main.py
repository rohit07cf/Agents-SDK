# main.py
import asyncio

from agent_tree import AgentNode, AgentTree
from tree import SimpleAgent, MathAgent, EchoAgent, ClassifierAgent
from supervisor import SupervisorAgent

from agents import Runner  # OpenAI Agents SDK Runner


async def main():
    # ------------------------------------------------------------------
    # CREATE SUPERVISOR ROOT NODE (STRUCTURAL TREE)
    # ------------------------------------------------------------------
    supervisor_node = AgentNode("Supervisor")

    # ------------------------------------------------------------------
    # CREATE AGENTS
    # ------------------------------------------------------------------
    simple_agent_node = supervisor_node.add_child(
        AgentNode("SimpleAgent", agent=SimpleAgent())
    )
    math_agent_node = supervisor_node.add_child(
        AgentNode("MathAgent", agent=MathAgent())
    )
    echo_agent_node = supervisor_node.add_child(
        AgentNode("EchoAgent", agent=EchoAgent())
    )
    classifier_agent_node = supervisor_node.add_child(
        AgentNode("ClassifierAgent", agent=ClassifierAgent())
    )

    # ------------------------------------------------------------------
    # ATTACH TOOLS TO EACH AGENT
    # ------------------------------------------------------------------
    # SimpleAgent
    simple_agent_node.add_tool("add_numbers")
    simple_agent_node.add_tool("echo_text")

    # MathAgent
    math_agent_node.add_tool("add_numbers")
    math_agent_node.add_tool("subtract_numbers")
    math_agent_node.add_tool("multiply_numbers")

    # EchoAgent
    echo_agent_node.add_tool("echo_text")
    echo_agent_node.add_tool("reverse_text")

    # ClassifierAgent
    classifier_agent_node.add_tool("classify_intent")
    classifier_agent_node.add_tool("detect_sentiment")

    # ------------------------------------------------------------------
    # BUILD FINAL AGENT TREE
    # ------------------------------------------------------------------
    tree = AgentTree(root=supervisor_node)

    # Visualize the structure
    tree.visualize()

    # ------------------------------------------------------------------
    # USE OPENAI AGENTS SDK SUPERVISOR + Runner.run
    # ------------------------------------------------------------------
    user_message = "Please add the numbers 10 and 32"

    # LLM supervisor – real OpenAI agent
    supervisor_agent = SupervisorAgent()

    sup_result = await Runner.run(
        starting_agent=supervisor_agent,
        input=user_message,
    )
    sup_decision = str(sup_result.final_output)
    print("\n🤖 SUPERVISOR LLM DECISION:", sup_decision)

    # Naive router: just pick MathAgent if supervisor mentioned it,
    # otherwise fall back to SimpleAgent (you can make this smarter).
    chosen_node = simple_agent_node
    if "MathAgent" in sup_decision:
        chosen_node = math_agent_node
    elif "EchoAgent" in sup_decision:
        chosen_node = echo_agent_node
    elif "ClassifierAgent" in sup_decision:
        chosen_node = classifier_agent_node

    print(f"\n🚀 RUNNING CHILD AGENT: {chosen_node.name}")
    final_result = await chosen_node.agent.run(user_message)

    print("\nFINAL RESULT FROM CHILD AGENT:")
    print(final_result)


if __name__ == "__main__":
    asyncio.run(main())
