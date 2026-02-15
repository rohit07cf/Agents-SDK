"""
schemas.py - Pydantic configs + output contracts.

Two sections:
  1) Configuration models  -> how agents are built
  2) Output contracts       -> what agents return (validated)

Follows the same config-driven pattern as configurable_agent/models.py
but adds full agent-creation configs (model, prompt, tools, handoffs).
"""

from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field


# ── Section 1: Configuration Models ─────────────────────────────────


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
    handoff_targets: List[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class TreeConfig(BaseModel):
    """
    Full multi-agent tree specification.
    - supervisor: the root agent
    - children: list of child agent configs
    """
    supervisor: AgentConfig
    children: List[AgentConfig] = Field(default_factory=list)


# ── Section 2: Output Contracts ──────────────────────────────────────


class HandoffResult(BaseModel):
    """
    Structured output for the HANDOFF pattern.

    Returned by a child agent after the supervisor
    transfers control to it.
    """
    from_agent: str
    to_agent: str
    status: Literal["success", "needs_more_info", "failed"]
    summary: str
    payload: Dict = Field(default_factory=dict)
    artifacts: List[str] = Field(default_factory=list)


class ToolResponse(BaseModel):
    """
    Structured output for the AGENT-AS-TOOL pattern.

    Returned when a child agent is invoked as a
    bounded tool call by the parent.
    """
    tool_name: str
    result: str
    metadata: Dict = Field(default_factory=dict)
