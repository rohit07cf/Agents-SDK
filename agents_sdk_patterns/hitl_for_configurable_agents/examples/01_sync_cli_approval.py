"""
01_sync_cli_approval.py - Sync CLI HITL demo.

Scenario:
  An agent wants to call "send_email".
  The HITL policy says send_email is HIGH risk.
  The agent must get human approval via terminal prompt.

Flow:
  Agent -> HITL policy check -> "needs approval" ->
  prompt human in CLI -> approve/deny -> execute or stop

Run:
  cd agents_sdk_patterns/hitl_for_configurable_agents
  python examples/01_sync_cli_approval.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from schemas import AgentConfig, HITLConfig, HITLRule, ModelConfig, PromptConfig
from configurable_agent_factory import (
    create_agent_from_config,
    execute_tool_with_hitl,
    register_tool,
)
from approval_store import InMemoryApprovalStore


# ── Step 1: Define tools ────────────────────────────────────────────

def send_email(to: str, subject: str, body: str) -> str:
    """Simulate sending an email (would call SMTP in production)."""
    return f"Email sent to {to}: [{subject}] {body}"


def read_data(query: str) -> str:
    """Simulate reading data (low risk, no side effects)."""
    return f"Query result for '{query}': 42 rows returned"


register_tool("send_email", send_email)
register_tool("read_data", read_data)


# ── Step 2: Configure agent + HITL (Pydantic) ──────────────────────

agent_config = AgentConfig(
    name="AssistantAgent",
    role="assistant",
    model_config=ModelConfig(model_name="gpt-4.1-mini"),
    prompt_config=PromptConfig(
        system_template="You help users by sending emails and querying data."
    ),
    tools=["send_email", "read_data"],
)

hitl_config = HITLConfig(
    enabled=True,
    mode="sync_cli",           # <-- human approves in terminal
    default_timeout_seconds=120,
    rules=[
        HITLRule(
            tool_name="send_email",
            action_type="send",
            risk_level="high",     # <-- email = high risk, always needs approval
            require_approval=True,
        ),
        HITLRule(
            tool_name="read_data",
            action_type="read",
            risk_level="low",
            require_approval=False,  # <-- reads are safe, no approval
        ),
    ],
)


# ── Step 3: Run the demo ────────────────────────────────────────────

def main():
    agent = create_agent_from_config(agent_config)
    store = InMemoryApprovalStore()

    print("=" * 60)
    print("SYNC CLI APPROVAL DEMO")
    print("=" * 60)

    # Tool 1: read_data (low risk, should auto-pass policy)
    print("\n--- Tool Call 1: read_data (low risk) ---")
    result1 = execute_tool_with_hitl(
        agent_name=agent.name,
        tool_name="read_data",
        tool_args={"query": "SELECT * FROM users LIMIT 10"},
        hitl_config=hitl_config,
        store=store,
    )
    print(f"  Result: {result1['result']}")
    print(f"  Executed: {result1['executed']}")

    # Tool 2: send_email (high risk, requires human approval)
    print("\n--- Tool Call 2: send_email (high risk) ---")
    result2 = execute_tool_with_hitl(
        agent_name=agent.name,
        tool_name="send_email",
        tool_args={
            "to": "ceo@company.com",
            "subject": "Q4 Report",
            "body": "Please find the Q4 report attached.",
        },
        hitl_config=hitl_config,
        store=store,
    )
    print(f"  Result: {result2['result']}")
    print(f"  Executed: {result2['executed']}")
    if result2["hitl_decision"]:
        print(f"  Decision: {result2['hitl_decision']['status']}")

    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
