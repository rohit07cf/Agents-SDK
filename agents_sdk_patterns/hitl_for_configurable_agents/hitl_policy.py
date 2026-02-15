"""
hitl_policy.py - Decides whether a tool call needs human approval.

This is the "gatekeeper" that sits between the agent and tool execution.
It checks the HITLConfig rules and returns a verdict:
  - needs_approval=True  -> agent must call the HITL tool first
  - needs_approval=False -> tool can execute directly

Kept minimal: one class, one method, no over-abstraction.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from schemas import HITLConfig, HITLRule


class PolicyVerdict:
    """What the policy decided for a specific tool call."""

    def __init__(
        self,
        needs_approval: bool,
        matched_rule: Optional[HITLRule] = None,
        risk_level: str = "low",
        reason: str = "",
    ):
        self.needs_approval = needs_approval
        self.matched_rule = matched_rule
        self.risk_level = risk_level
        self.reason = reason

    def __repr__(self) -> str:
        return (
            f"PolicyVerdict(needs_approval={self.needs_approval}, "
            f"risk={self.risk_level}, reason={self.reason!r})"
        )


class HITLPolicy:
    """
    Evaluates whether a tool call requires human approval.

    How it works:
      1. Look up the tool_name in the config rules
      2. If a matching rule exists and require_approval=True -> needs approval
      3. If auto_approve_if conditions are met -> skip approval
      4. If no rule matches -> no approval needed (default-allow)

    Usage:
        policy = HITLPolicy(hitl_config)
        verdict = policy.evaluate("send_email", {"to": "ceo@company.com"})
        if verdict.needs_approval:
            # call HITL tool
    """

    def __init__(self, config: HITLConfig):
        self.config = config
        # Index rules by tool_name for O(1) lookup
        self._rules_by_tool: Dict[str, HITLRule] = {
            rule.tool_name: rule for rule in config.rules
        }

    def evaluate(self, tool_name: str, tool_args: Dict[str, Any] = None) -> PolicyVerdict:
        """
        Check if this tool call needs approval.

        Returns PolicyVerdict with the decision + reasoning.
        """
        tool_args = tool_args or {}

        # HITL disabled globally -> everything passes
        if not self.config.enabled:
            return PolicyVerdict(
                needs_approval=False,
                reason="HITL disabled globally",
            )

        # No rule for this tool -> default allow
        rule = self._rules_by_tool.get(tool_name)
        if rule is None:
            return PolicyVerdict(
                needs_approval=False,
                reason=f"No HITL rule for tool '{tool_name}'",
            )

        # Rule exists but approval not required
        if not rule.require_approval:
            return PolicyVerdict(
                needs_approval=False,
                matched_rule=rule,
                risk_level=rule.risk_level,
                reason=f"Rule exists but require_approval=False",
            )

        # Check auto-approve conditions (simple key-value matching)
        if rule.auto_approve_if and self._check_auto_approve(rule, tool_args):
            return PolicyVerdict(
                needs_approval=False,
                matched_rule=rule,
                risk_level=rule.risk_level,
                reason=f"Auto-approved: conditions met ({rule.auto_approve_if})",
            )

        # Approval required
        return PolicyVerdict(
            needs_approval=True,
            matched_rule=rule,
            risk_level=rule.risk_level,
            reason=f"Rule requires approval for '{tool_name}' (risk={rule.risk_level})",
        )

    def _check_auto_approve(self, rule: HITLRule, tool_args: Dict[str, Any]) -> bool:
        """
        Simple condition matching: every key in auto_approve_if
        must match the corresponding value in tool_args.

        Example:
            auto_approve_if={"max_amount": 100}
            tool_args={"amount": 50}  -> True (50 <= 100)

            auto_approve_if={"recipient_domain": "internal.com"}
            tool_args={"recipient_domain": "internal.com"}  -> True
        """
        for key, expected in rule.auto_approve_if.items():
            actual = tool_args.get(key)
            if actual is None:
                return False

            # Numeric ceiling check: auto-approve if actual <= expected
            if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
                if actual > expected:
                    return False
            # String equality check
            elif str(actual) != str(expected):
                return False

        return True
