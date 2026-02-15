"""
schemas.py - Pydantic configs + contracts for HITL (Human-in-the-Loop).

Three sections:
  1) Agent configs  -> reused from configurable_agent patterns
  2) HITL configs   -> how HITL is configured per agent/tool
  3) HITL contracts -> what flows between agent <-> human <-> store

Every HITL interaction is validated through Pydantic.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Section 1: Agent Configuration (same pattern as configurable_agent/)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class ModelConfig(BaseModel):
    """LLM provider + model settings."""
    provider: str = "openai"
    model_name: str = "gpt-4.1-mini"
    temperature: float = 0.0
    max_tokens: int = 1024


class PromptConfig(BaseModel):
    """Prompt templates for an agent."""
    system_template: str = "You are a helpful agent."
    user_template: str = "{input}"


class AgentConfig(BaseModel):
    """Everything needed to instantiate one agent."""
    name: str
    role: str = "general"
    model_config_: ModelConfig = Field(default_factory=ModelConfig, alias="model_config")
    prompt_config: PromptConfig = Field(default_factory=PromptConfig)
    tools: List[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Section 2: HITL Configuration
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class HITLRule(BaseModel):
    """
    One rule that maps a tool + action to a risk level + approval requirement.

    Example:
        HITLRule(tool_name="send_email", action_type="send",
                 risk_level="high", require_approval=True)
    """
    tool_name: str
    action_type: str = "execute"
    risk_level: Literal["low", "medium", "high"] = "medium"
    require_approval: bool = True
    auto_approve_if: Dict[str, Any] = Field(default_factory=dict)


class HITLConfig(BaseModel):
    """
    Top-level HITL configuration attached to an agent.

    Controls:
      - whether HITL is enabled at all
      - which mode to use (sync CLI, async queue, auto rules)
      - timeout, escalation, and per-tool rules
    """
    enabled: bool = True
    mode: Literal["sync_cli", "async_queue", "auto_rules"] = "sync_cli"
    default_timeout_seconds: int = 60
    escalation_enabled: bool = False
    approver_group: str = "default"
    rules: List[HITLRule] = Field(default_factory=list)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Section 3: HITL Contracts (request + decision)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class ApprovalRequest(BaseModel):
    """
    Created by the agent when a tool call needs human approval.

    Sent to the HITL tool / approval store for a human to review.
    """
    request_id: str
    agent_name: str
    tool_name: str
    tool_args: Dict[str, Any] = Field(default_factory=dict)
    risk_level: str = "medium"
    created_at: datetime = Field(default_factory=datetime.now)
    reason: str = ""


class ApprovalDecision(BaseModel):
    """
    The human's response to an ApprovalRequest.

    status values:
      - approved:        go ahead, execute the tool
      - denied:          do NOT execute, agent must pick alternative
      - needs_more_info: agent should clarify and re-request
      - escalated:       routed to a higher authority
      - timeout:         no response within deadline
    """
    request_id: str
    status: Literal["approved", "denied", "needs_more_info", "escalated", "timeout"]
    human_comment: Optional[str] = None
    constraints: Dict[str, Any] = Field(default_factory=dict)
    edited_tool_args: Optional[Dict[str, Any]] = None
    decided_at: datetime = Field(default_factory=datetime.now)
