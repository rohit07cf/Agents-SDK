# state.py
from __future__ import annotations
from typing import Any, Dict, List, Optional, TypedDict, Literal

Decision = Literal["approve", "revise", "cancel"]

class PendingToolCall(TypedDict, total=False):
    tool_name: str
    tool_args: Dict[str, Any]
    rationale: str
    request_id: str  # stable id for the pending action

class HumanInput(TypedDict, total=False):
    decision: Decision
    revised_args: Dict[str, Any]
    note: str

class GraphState(TypedDict, total=False):
    messages: List[Dict[str, Any]]          # your chat messages
    pending_tool: Optional[PendingToolCall] # set right before tool execution
    human_input: Optional[HumanInput]       # set when human responds
    last_tool_result: Optional[Any]
