"""
02_async_queue_approval.py - Async queue-based HITL demo.

Scenario:
  Agent creates a "delete_records" approval request.
  Request goes to a store (simulated queue).
  A separate "approver" thread writes a decision.
  Agent polls and proceeds when decision arrives.

No external services needed -- uses InMemoryApprovalStore + threading.

Run:
  cd agents_sdk_patterns/hitl_for_configurable_agents
  python examples/02_async_queue_approval.py
"""

import sys
import os
import threading
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime

from schemas import (
    AgentConfig,
    ApprovalDecision,
    HITLConfig,
    HITLRule,
    ModelConfig,
    PromptConfig,
)
from configurable_agent_factory import (
    create_agent_from_config,
    execute_tool_with_hitl,
    register_tool,
)
from approval_store import InMemoryApprovalStore


# ── Step 1: Define tools ────────────────────────────────────────────

def delete_records(table: str, where: str) -> str:
    """Simulate deleting records (destructive, needs approval)."""
    return f"Deleted records from '{table}' WHERE {where}"


def count_records(table: str) -> str:
    """Simulate counting records (safe read)."""
    return f"Table '{table}' has 1,234 records"


register_tool("delete_records", delete_records)
register_tool("count_records", count_records)


# ── Step 2: Configure agent + HITL ─────────────────────────────────

agent_config = AgentConfig(
    name="DataAgent",
    role="data-manager",
    model_config=ModelConfig(model_name="gpt-4.1-mini"),
    prompt_config=PromptConfig(
        system_template="You manage data operations. Deletions need approval."
    ),
    tools=["delete_records", "count_records"],
)

hitl_config = HITLConfig(
    enabled=True,
    mode="async_queue",          # <-- async: write to store, poll for decision
    default_timeout_seconds=10,  # short timeout for demo
    rules=[
        HITLRule(
            tool_name="delete_records",
            action_type="delete",
            risk_level="high",
            require_approval=True,
        ),
    ],
)


# ── Step 3: Simulate an external approver ───────────────────────────

def simulate_approver(store: InMemoryApprovalStore, delay_seconds: float = 2.0):
    """
    Runs in a separate thread.
    Waits for pending requests and auto-approves them.
    Simulates a human approver or approval service.
    """
    time.sleep(delay_seconds)  # simulate human thinking time

    pending = store.list_pending()
    for req in pending:
        print(f"\n  [Approver] Reviewing request {req.request_id}...")
        print(f"  [Approver] Tool: {req.tool_name}, Args: {req.tool_args}")

        decision = ApprovalDecision(
            request_id=req.request_id,
            status="approved",
            human_comment="Approved by async reviewer after inspection",
            constraints={"max_rows": 100},  # <-- add a constraint
        )
        store.save_decision(decision)
        print(f"  [Approver] Decision: APPROVED (with max_rows=100 constraint)")


# ── Step 4: Run the demo ────────────────────────────────────────────

def main():
    agent = create_agent_from_config(agent_config)
    store = InMemoryApprovalStore()

    print("=" * 60)
    print("ASYNC QUEUE APPROVAL DEMO")
    print("=" * 60)

    # Tool 1: count_records (no rule, passes directly)
    print("\n--- Tool Call 1: count_records (no HITL rule) ---")
    result1 = execute_tool_with_hitl(
        agent_name=agent.name,
        tool_name="count_records",
        tool_args={"table": "users"},
        hitl_config=hitl_config,
        store=store,
    )
    print(f"  Result: {result1['result']}")

    # Tool 2: delete_records (high risk, async approval)
    print("\n--- Tool Call 2: delete_records (high risk, async) ---")

    # Launch approver in background thread BEFORE calling tool
    # (simulates an external approver watching the queue)
    approver_thread = threading.Thread(
        target=simulate_approver,
        args=(store, 2.0),  # 2 second delay
    )
    approver_thread.start()

    result2 = execute_tool_with_hitl(
        agent_name=agent.name,
        tool_name="delete_records",
        tool_args={"table": "temp_logs", "where": "created_at < '2024-01-01'"},
        hitl_config=hitl_config,
        store=store,
    )

    approver_thread.join()

    print(f"\n  Result:   {result2['result']}")
    print(f"  Executed: {result2['executed']}")
    if result2["hitl_decision"]:
        print(f"  Decision: {result2['hitl_decision']['status']}")
        if result2["hitl_decision"].get("constraints"):
            print(f"  Constraints: {result2['hitl_decision']['constraints']}")

    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
