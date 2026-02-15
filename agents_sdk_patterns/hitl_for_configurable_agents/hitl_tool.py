"""
hitl_tool.py - The HITL tool that agents call to request human approval.

Tool name: request_human_approval

This is the CORE of the HITL pattern:
  - Agent creates an ApprovalRequest
  - Tool routes it based on mode (sync_cli / async_queue / auto_rules)
  - Human (or auto-rule) produces an ApprovalDecision
  - Decision is returned to the agent as structured Pydantic output

Three modes:
  sync_cli     -> prompts human in terminal right now
  async_queue  -> writes to store, polls until decision arrives
  auto_rules   -> auto-approve/deny based on risk rules (no human)
"""

from __future__ import annotations

from datetime import datetime
from typing import Callable, Optional

from schemas import ApprovalDecision, ApprovalRequest, HITLConfig, HITLRule
from approval_store import InMemoryApprovalStore


def request_human_approval(
    request: ApprovalRequest,
    config: HITLConfig,
    store: Optional[InMemoryApprovalStore] = None,
    input_fn: Optional[Callable[[str], str]] = None,
) -> ApprovalDecision:
    """
    The HITL tool. Routes approval based on config.mode.

    Args:
        request:  what the agent wants approved
        config:   HITL configuration (mode, timeout, rules)
        store:    approval store (required for async_queue)
        input_fn: override for input() -- useful for testing

    Returns:
        ApprovalDecision (always Pydantic-validated)
    """
    # Always persist the request
    if store:
        store.save_request(request)

    if config.mode == "sync_cli":
        decision = _handle_sync_cli(request, config, input_fn)
    elif config.mode == "async_queue":
        decision = _handle_async_queue(request, config, store)
    elif config.mode == "auto_rules":
        decision = _handle_auto_rules(request, config)
    else:
        # Unknown mode -> safe default: deny
        decision = ApprovalDecision(
            request_id=request.request_id,
            status="denied",
            human_comment=f"Unknown HITL mode: {config.mode}",
        )

    # Always persist the decision
    if store:
        store.save_decision(decision)

    return decision


# ── Mode 1: Sync CLI ────────────────────────────────────────────────


def _handle_sync_cli(
    request: ApprovalRequest,
    config: HITLConfig,
    input_fn: Optional[Callable[[str], str]] = None,
) -> ApprovalDecision:
    """
    Prompt human in terminal. Blocking.

    Shows the request details and asks: approve / deny / edit args.
    """
    _input = input_fn or input

    print("\n" + "=" * 55)
    print("  HUMAN APPROVAL REQUIRED")
    print("=" * 55)
    print(f"  Request ID:  {request.request_id}")
    print(f"  Agent:       {request.agent_name}")
    print(f"  Tool:        {request.tool_name}")
    print(f"  Risk Level:  {request.risk_level}")
    print(f"  Reason:      {request.reason}")
    print(f"  Tool Args:   {request.tool_args}")
    print("-" * 55)

    choice = _input("  Decision [a]pprove / [d]eny / [e]dit args: ").strip().lower()

    if choice in ("a", "approve"):
        return ApprovalDecision(
            request_id=request.request_id,
            status="approved",
            human_comment="Approved via CLI",
        )

    if choice in ("e", "edit"):
        # Let human edit specific args
        edited = dict(request.tool_args)
        for key, val in request.tool_args.items():
            new_val = _input(f"    {key} [{val}]: ").strip()
            if new_val:
                edited[key] = new_val
        return ApprovalDecision(
            request_id=request.request_id,
            status="approved",
            human_comment="Approved with edits via CLI",
            edited_tool_args=edited,
        )

    # Default: deny (covers 'd', 'deny', and anything unexpected)
    comment = _input("  Denial reason (optional): ").strip() or "Denied via CLI"
    return ApprovalDecision(
        request_id=request.request_id,
        status="denied",
        human_comment=comment,
    )


# ── Mode 2: Async Queue ────────────────────────────────────────────


def _handle_async_queue(
    request: ApprovalRequest,
    config: HITLConfig,
    store: Optional[InMemoryApprovalStore] = None,
) -> ApprovalDecision:
    """
    Write request to store, then poll for decision.

    In production this would be a webhook/queue.
    Here we poll the store until decision appears or timeout.
    """
    if store is None:
        return ApprovalDecision(
            request_id=request.request_id,
            status="denied",
            human_comment="No store configured for async_queue mode",
        )

    # Request already saved by caller. Now poll.
    print(f"  [async] Waiting for approval (timeout={config.default_timeout_seconds}s)...")

    decision = store.wait_for_decision(
        request.request_id,
        timeout_seconds=config.default_timeout_seconds,
    )

    if decision is None:
        # Timeout -> safe deny
        return ApprovalDecision(
            request_id=request.request_id,
            status="timeout",
            human_comment=f"No response within {config.default_timeout_seconds}s",
        )

    return decision


# ── Mode 3: Auto Rules ─────────────────────────────────────────────


def _handle_auto_rules(
    request: ApprovalRequest,
    config: HITLConfig,
) -> ApprovalDecision:
    """
    Auto-approve or deny based on risk_level rules.

    Logic:
      - low risk  -> auto-approve
      - high risk -> auto-deny (needs real human)
      - medium    -> check auto_approve_if conditions
    """
    # Find the matching rule
    matched_rule: Optional[HITLRule] = None
    for rule in config.rules:
        if rule.tool_name == request.tool_name:
            matched_rule = rule
            break

    if matched_rule is None:
        # No rule -> default approve for auto_rules mode
        return ApprovalDecision(
            request_id=request.request_id,
            status="approved",
            human_comment="No rule matched, auto-approved",
        )

    risk = matched_rule.risk_level

    if risk == "low":
        return ApprovalDecision(
            request_id=request.request_id,
            status="approved",
            human_comment=f"Auto-approved: risk_level=low for '{request.tool_name}'",
        )

    if risk == "high":
        return ApprovalDecision(
            request_id=request.request_id,
            status="denied",
            human_comment=f"Auto-denied: risk_level=high for '{request.tool_name}' requires human",
        )

    # Medium: check auto_approve_if conditions
    if matched_rule.auto_approve_if:
        all_met = all(
            str(request.tool_args.get(k)) == str(v)
            for k, v in matched_rule.auto_approve_if.items()
        )
        if all_met:
            return ApprovalDecision(
                request_id=request.request_id,
                status="approved",
                human_comment=f"Auto-approved: conditions met ({matched_rule.auto_approve_if})",
            )

    # Medium without matching conditions -> deny (safer)
    return ApprovalDecision(
        request_id=request.request_id,
        status="denied",
        human_comment=f"Auto-denied: medium risk, conditions not met for '{request.tool_name}'",
    )
