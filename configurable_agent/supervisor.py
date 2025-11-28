# supervisor.py
from agents import Agent as OAAgent
from models import SupervisorOutput


class SupervisorAgent(OAAgent):
    """
    LLM-based supervisor built directly on the OpenAI Agents SDK.

    It doesn't actually call your Python agents directly yet, but it will
    decide *which* agent is best and explain why. You can later wire this
    decision into your own router logic.
    """

    def __init__(self):
        super().__init__(
            name="Supervisor",
            instructions=(
                "You are a supervisor that routes user requests to a team of custom agents.\n\n"
                "Each agent has:\n"
                "- A name (e.g., 'MathAgent', 'SearchAgent', 'GuardAgent').\n"
                "- A specialization implied by its name and description.\n\n"
                "Your job for every user message is to:\n"
                "1) Infer the user's goal and what kind of capability is needed.\n"
                "2) Choose the single most suitable agent by its name.\n"
                "3) Briefly explain why that agent is appropriate.\n\n"
                "If no existing agent seems appropriate, choose 'Supervisor' and handle it yourself.\n\n"
                "Format your answer exactly as:\n"
                "AGENT_NAME: explanation..."
            ),
        )
