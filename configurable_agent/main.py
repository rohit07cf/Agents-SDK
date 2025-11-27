# # main.py
# import asyncio
# from agent_tree import AgentNode, AgentTree
# from tree import SimpleAgent  # our LLM agent class

# async def main():
#     # CREATE AGENT TREE HERE 👇
#     supervisor = AgentNode("Supervisor")
#     simple_agent_node = supervisor.add_child(AgentNode("SimpleAgent", agent=SimpleAgent()))

#     # Attach tools to SimpleAgent
#     simple_agent_node.add_tool("add_numbers")
#     simple_agent_node.add_tool("echo_text")

#     # Final agent tree object
#     tree = AgentTree(root=supervisor)

#     # Visualize in console
#     tree.visualize()

#     # Run agent
#     result = await simple_agent_node.agent.run("Please add the numbers")

# # Run event loop
# if __name__ == "__main__":
#     asyncio.run(main())











# main.py
import asyncio

from agent_tree import AgentNode, AgentTree
from tree import SimpleAgent, MathAgent, EchoAgent, ClassifierAgent
from supervisor import SupervisorAgent

async def main():
    # ------------------------------------------------------------------
    # CREATE SUPERVISOR ROOT NODE
    # ------------------------------------------------------------------
    supervisor = AgentNode("Supervisor")

    # ------------------------------------------------------------------
    # CREATE AGENTS
    # ------------------------------------------------------------------
    simple_agent_node = supervisor.add_child(AgentNode("SimpleAgent", agent=SimpleAgent()))
    math_agent_node = supervisor.add_child(AgentNode("MathAgent", agent=MathAgent()))
    echo_agent_node = supervisor.add_child(AgentNode("EchoAgent", agent=EchoAgent()))
    classifier_agent_node = supervisor.add_child(AgentNode("ClassifierAgent", agent=ClassifierAgent()))

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
    tree = AgentTree(root=supervisor)

    # Visualize structure
    tree.visualize()

    # Run agent
    result = await simple_agent_node.agent.run("Please add the numbers")
    print("\nFINAL RESULT:", result)


if __name__ == "__main__":
    asyncio.run(main())
