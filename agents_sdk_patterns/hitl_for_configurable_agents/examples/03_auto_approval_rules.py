"""
03_auto_approval_rules.py - Auto-approval rules demo.

Scenario:
  Agent calls multiple tools with different risk levels.
  HITL is in "auto_rules" mode -- no human in the loop at all.
  Rules decide automatically:
    - low risk   -> auto-approve
    - medium     -> auto-approve IF conditions met
    - high risk  -> auto-deny (would need real human)

This is useful for:
  - Dev/staging environments (don't block on human)
  - Known-safe operations that still need audit logging

Run:
  cd agents_sdk_patterns/hitl_for_configurable_agents
  python examples/03_auto_approval_rules.py
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

def log_event(message: str) -> str:
    """Write a log entry (safe, low risk)."""
    return f"Logged: {message}"


def transfer_funds(amount: float, to_account: str) -> str:
    """Transfer money (risky, needs approval)."""
    return f"Transferred ${amount} to {to_account}"


def update_config(key: str, value: str) -> str:
    """Update a config setting (medium risk)."""
    return f"Config updated: {key}={value}"


register_tool("log_event", log_event)
register_tool("transfer_funds", transfer_funds)
register_tool("update_config", update_config)


# ── Step 2: Configure auto-approval rules ──────────────────────────

agent_config = AgentConfig(
    name="FinanceAgent",
    role="finance",
    model_config=ModelConfig(model_name="gpt-4.1-mini"),
    prompt_config=PromptConfig(
        system_template="You handle financial operations and config updates."
    ),
    tools=["log_event", "transfer_funds", "update_config"],
)

hitl_config = HITLConfig(
    enabled=True,
    mode="auto_rules",  # <-- fully automated, no human prompt
    rules=[
        # Low risk: always auto-approve
        HITLRule(
            tool_name="log_event",
            action_type="write_log",
            risk_level="low",
            require_approval=True,  # rule exists, but auto_rules mode will approve low risk
        ),
        # High risk: always auto-deny (needs real human)
        HITLRule(
            tool_name="transfer_funds",
            action_type="transfer",
            risk_level="high",
            require_approval=True,
        ),
        # Medium risk: auto-approve IF key is in allowed list
        HITLRule(
            tool_name="update_config",
            action_type="update",
            risk_level="medium",
            require_approval=True,
            auto_approve_if={"key": "log_level"},  # only auto-approve log_level changes
        ),
    ],
)


# ── Step 3: Run the demo ────────────────────────────────────────────

def main():
    agent = create_agent_from_config(agent_config)
    store = InMemoryApprovalStore()

    print("=" * 60)
    print("AUTO-APPROVAL RULES DEMO")
    print("=" * 60)

    # Tool 1: log_event (low risk -> auto-approve)
    print("\n--- Tool Call 1: log_event (low risk) ---")
    r1 = execute_tool_with_hitl(
        agent_name=agent.name,
        tool_name="log_event",
        tool_args={"message": "User login from IP 10.0.0.1"},
        hitl_config=hitl_config,
        store=store,
    )
    print(f"  Result:   {r1['result']}")
    print(f"  Executed: {r1['executed']}")

    # Tool 2: transfer_funds (high risk -> auto-deny)
    print("\n--- Tool Call 2: transfer_funds (high risk) ---")
    r2 = execute_tool_with_hitl(
        agent_name=agent.name,
        tool_name="transfer_funds",
        tool_args={"amount": 50000.0, "to_account": "offshore-123"},
        hitl_config=hitl_config,
        store=store,
    )
    print(f"  Result:   {r2['result']}")
    print(f"  Executed: {r2['executed']}")
    if r2["hitl_decision"]:
        print(f"  Reason:   {r2['hitl_decision']['human_comment']}")

    # Tool 3: update_config with key=log_level (medium, conditions MET -> approve)
    print("\n--- Tool Call 3: update_config key=log_level (medium, conditions met) ---")
    r3 = execute_tool_with_hitl(
        agent_name=agent.name,
        tool_name="update_config",
        tool_args={"key": "log_level", "value": "DEBUG"},
        hitl_config=hitl_config,
        store=store,
    )
    print(f"  Result:   {r3['result']}")
    print(f"  Executed: {r3['executed']}")

    # Tool 4: update_config with key=db_password (medium, conditions NOT met -> deny)
    print("\n--- Tool Call 4: update_config key=db_password (medium, conditions NOT met) ---")
    r4 = execute_tool_with_hitl(
        agent_name=agent.name,
        tool_name="update_config",
        tool_args={"key": "db_password", "value": "hunter2"},
        hitl_config=hitl_config,
        store=store,
    )
    print(f"  Result:   {r4['result']}")
    print(f"  Executed: {r4['executed']}")
    if r4["hitl_decision"]:
        print(f"  Reason:   {r4['hitl_decision']['human_comment']}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  log_event       (low):    {'EXECUTED' if r1['executed'] else 'BLOCKED'}")
    print(f"  transfer_funds  (high):   {'EXECUTED' if r2['executed'] else 'BLOCKED'}")
    print(f"  update_config   (med/ok): {'EXECUTED' if r3['executed'] else 'BLOCKED'}")
    print(f"  update_config   (med/no): {'EXECUTED' if r4['executed'] else 'BLOCKED'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
