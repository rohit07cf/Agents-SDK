# Agents

- Agents are the core building block in your apps. An agent is a large language model (LLM), configured with instructions and tools.

Basic configuration
- The most common properties of an agent you'll configure are:
    - **instructions**: also known as a developer message or system prompt.
    - **model**: which LLM to use, and optional model_settings to configure model tuning parameters like temperature, top_p, etc.
    - **tools**: Tools that the agent can use to achieve its tasks.