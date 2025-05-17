# Agents-SDK
OpenAI Agents SDK
- The OpenAI Agents SDK enables you to build **agentic AI apps** in a **lightweight, easy-to-use package** with very few abstractions.
- It's a production-ready upgrade of our previous experimentation for agents, **Swarm**.
- The Agents SDK has a very small set of primitives:
    - **Agents** , which are LLMs equipped with instructions and tools
    - **Handoffs**, which allow agents to delegate to other agents for specific tasks
    - **Guardrails**, which enable the inputs to agents to be validated
- Main features of the SDK:
    - **Agent loop**: Built-in agent loop that handles calling tools, sending results to the LLM, and **looping** until the LLM is done.
    - **Python-first**: Use built-in language features to **orchestrate and chain agents**, rather than needing to learn new abstractions.
    - **Handoffs**: A powerful feature to **coordinate** and **delegate between multiple agents**.
    - **Guardrails**: Run input validations and checks in parallel to your agents, breaking early if the checks fail.
    - **Function tools**: Turn any Python function into a tool, with automatic schema generation and **Pydantic-powered validation**.
    - **Tracing**: **Built-in tracing** that lets you visualize, debug and monitor your workflows, as well as use the OpenAI suite of evaluation, fine-tuning and distillation tools.   


# Multi-agent supervisor

- **Supervisor** is a multi-agent architecture where specialized agents are coordinated by a central supervisor agent. 
- The supervisor agent controls all **communication flow** and **task delegation**, making decisions about **which agent to invoke** based on the **current context and task requirements**.
- Build a supervisor for orchestrating child agents with the prebuilt **langgraph-supervisor**


# STEPS:

1. Create worker agents - create specialized worker agents
    - To create individual worker agents, we will use LangGraph's prebuilt **agent**.
2. Create supervisor with **langgraph-supervisor**
3. To implement multi-agent system, use **create_supervisor** from the prebuilt **langgraph-supervisor** library