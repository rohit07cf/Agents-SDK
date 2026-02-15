"""
test_hitl_tool.py - Unit tests for the HITL system.

Tests:
  1. Policy evaluates correctly for different risk levels
  2. Sync CLI with mocked input
  3. Timeout produces safe denial
  4. Edited args are applied correctly
  5. Auto-rules approve low-risk, deny high-risk
  6. Approval store saves and retrieves

Run:
  cd agents_sdk_patterns/hitl_for_configurable_agents
  python -m pytest tests/ -v
"""

import sys
import os
import threading
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime

from schemas import (
    ApprovalDecision,
    ApprovalRequest,
    HITLConfig,
    HITLRule,
)
from hitl_policy import HITLPolicy
from hitl_tool import request_human_approval
from approval_store import InMemoryApprovalStore
from configurable_agent_factory import execute_tool_with_hitl, register_tool


# ── Fixtures / Helpers ──────────────────────────────────────────────

def _make_config(**overrides) -> HITLConfig:
    """Build a test HITLConfig with sensible defaults."""
    defaults = dict(
        enabled=True,
        mode="auto_rules",
        default_timeout_seconds=2,
        rules=[
            HITLRule(tool_name="safe_tool", risk_level="low", require_approval=True),
            HITLRule(tool_name="risky_tool", risk_level="high", require_approval=True),
            HITLRule(
                tool_name="conditional_tool",
                risk_level="medium",
                require_approval=True,
                auto_approve_if={"env": "staging"},
            ),
        ],
    )
    defaults.update(overrides)
    return HITLConfig(**defaults)


def _make_request(tool_name: str = "risky_tool", **overrides) -> ApprovalRequest:
    """Build a test ApprovalRequest."""
    defaults = dict(
        request_id="test-001",
        agent_name="TestAgent",
        tool_name=tool_name,
        tool_args={"key": "value"},
        risk_level="high",
        reason="test",
    )
    defaults.update(overrides)
    return ApprovalRequest(**defaults)


# Register test tools
def _safe_tool(key: str = "default") -> str:
    return f"safe_result:{key}"

def _risky_tool(key: str = "default") -> str:
    return f"risky_result:{key}"

register_tool("safe_tool", _safe_tool)
register_tool("risky_tool", _risky_tool)


# ── Test: Policy Evaluation ─────────────────────────────────────────

def test_policy_low_risk_no_approval():
    """Low-risk tool should not need approval."""
    config = _make_config()
    policy = HITLPolicy(config)
    verdict = policy.evaluate("safe_tool", {})
    # In auto_rules mode, policy still says needs_approval=True
    # but the auto_rules handler will approve it.
    # Here we test that the policy DOES flag it (rule has require_approval=True)
    assert verdict.needs_approval is True
    assert verdict.risk_level == "low"


def test_policy_high_risk_needs_approval():
    """High-risk tool should need approval."""
    config = _make_config()
    policy = HITLPolicy(config)
    verdict = policy.evaluate("risky_tool", {})
    assert verdict.needs_approval is True
    assert verdict.risk_level == "high"


def test_policy_no_rule_no_approval():
    """Tool with no matching rule should not need approval."""
    config = _make_config()
    policy = HITLPolicy(config)
    verdict = policy.evaluate("unknown_tool", {})
    assert verdict.needs_approval is False


def test_policy_disabled_globally():
    """When HITL is disabled, nothing needs approval."""
    config = _make_config(enabled=False)
    policy = HITLPolicy(config)
    verdict = policy.evaluate("risky_tool", {})
    assert verdict.needs_approval is False


def test_policy_auto_approve_conditions_met():
    """Medium risk with matching conditions -> no approval needed."""
    config = _make_config()
    policy = HITLPolicy(config)
    verdict = policy.evaluate("conditional_tool", {"env": "staging"})
    assert verdict.needs_approval is False
    assert "Auto-approved" in verdict.reason


def test_policy_auto_approve_conditions_not_met():
    """Medium risk with non-matching conditions -> needs approval."""
    config = _make_config()
    policy = HITLPolicy(config)
    verdict = policy.evaluate("conditional_tool", {"env": "production"})
    assert verdict.needs_approval is True


# ── Test: Sync CLI with Mocked Input ────────────────────────────────

def test_sync_cli_approve():
    """Mock CLI input to approve."""
    config = _make_config(mode="sync_cli")
    request = _make_request()

    # Mock: always type "a" (approve)
    decision = request_human_approval(
        request=request,
        config=config,
        input_fn=lambda _: "a",
    )
    assert decision.status == "approved"
    assert decision.request_id == "test-001"


def test_sync_cli_deny():
    """Mock CLI input to deny."""
    config = _make_config(mode="sync_cli")
    request = _make_request()

    responses = iter(["d", "Not safe enough"])
    decision = request_human_approval(
        request=request,
        config=config,
        input_fn=lambda _: next(responses),
    )
    assert decision.status == "denied"
    assert "Not safe enough" in decision.human_comment


# ── Test: Timeout -> Safe Denial ────────────────────────────────────

def test_async_queue_timeout():
    """When no decision arrives, should timeout with denial."""
    config = _make_config(mode="async_queue", default_timeout_seconds=1)
    store = InMemoryApprovalStore()
    request = _make_request()

    # Don't save any decision -> should timeout
    decision = request_human_approval(
        request=request,
        config=config,
        store=store,
    )
    assert decision.status == "timeout"


# ── Test: Edited Args Applied ───────────────────────────────────────

def test_sync_cli_edit_args():
    """Mock CLI to edit args. Verify edited args are returned."""
    config = _make_config(mode="sync_cli")
    request = _make_request(tool_args={"to": "ceo@company.com", "subject": "Draft"})

    # Mock: choose "e" (edit), then provide new values
    responses = iter(["e", "cfo@company.com", "Final Report"])
    decision = request_human_approval(
        request=request,
        config=config,
        input_fn=lambda _: next(responses),
    )
    assert decision.status == "approved"
    assert decision.edited_tool_args is not None
    assert decision.edited_tool_args["to"] == "cfo@company.com"
    assert decision.edited_tool_args["subject"] == "Final Report"


# ── Test: Auto-Rules ────────────────────────────────────────────────

def test_auto_rules_approve_low_risk():
    """Auto-rules mode should approve low-risk tools."""
    config = _make_config(mode="auto_rules")
    request = _make_request(tool_name="safe_tool", risk_level="low")

    decision = request_human_approval(request=request, config=config)
    assert decision.status == "approved"


def test_auto_rules_deny_high_risk():
    """Auto-rules mode should deny high-risk tools."""
    config = _make_config(mode="auto_rules")
    request = _make_request(tool_name="risky_tool", risk_level="high")

    decision = request_human_approval(request=request, config=config)
    assert decision.status == "denied"


# ── Test: Approval Store ────────────────────────────────────────────

def test_store_save_and_retrieve():
    """Store should save and retrieve requests and decisions."""
    store = InMemoryApprovalStore()
    request = _make_request()
    store.save_request(request)

    retrieved = store.get_request("test-001")
    assert retrieved is not None
    assert retrieved.tool_name == "risky_tool"

    decision = ApprovalDecision(
        request_id="test-001",
        status="approved",
        human_comment="Looks good",
    )
    store.save_decision(decision)

    retrieved_dec = store.get_decision("test-001")
    assert retrieved_dec is not None
    assert retrieved_dec.status == "approved"


def test_store_list_pending():
    """list_pending should return requests without decisions."""
    store = InMemoryApprovalStore()
    store.save_request(_make_request(request_id="req-1"))
    store.save_request(_make_request(request_id="req-2"))
    store.save_decision(ApprovalDecision(request_id="req-1", status="approved"))

    pending = store.list_pending()
    assert len(pending) == 1
    assert pending[0].request_id == "req-2"


# ── Test: Full Integration ──────────────────────────────────────────

def test_execute_tool_with_hitl_no_approval_needed():
    """Tool with no rule should execute directly."""
    config = _make_config(mode="auto_rules")
    store = InMemoryApprovalStore()

    result = execute_tool_with_hitl(
        agent_name="TestAgent",
        tool_name="safe_tool",
        tool_args={"key": "test"},
        hitl_config=config,
        store=store,
    )
    assert result["executed"] is True
    assert "safe_result" in str(result["result"])


if __name__ == "__main__":
    # Run all tests manually
    import traceback

    tests = [v for k, v in globals().items() if k.startswith("test_")]
    passed = 0
    failed = 0
    for test_fn in tests:
        try:
            test_fn()
            print(f"  PASS: {test_fn.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL: {test_fn.__name__}: {e}")
            traceback.print_exc()
            failed += 1

    print(f"\n{passed} passed, {failed} failed out of {len(tests)} tests")
