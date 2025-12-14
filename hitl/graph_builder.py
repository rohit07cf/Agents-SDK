# graph_builder.py
from __future__ import annotations
import uuid
from typing import Any, Dict, Literal

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command

from state import GraphState
from tools import TOOLS

# -------------------------
# Supervisor (orchestrator)
# -------------------------
def supervisor_node(state: GraphState) -> GraphState:
    """
    Decide the next action. In real life this is an LLM call that outputs
    a tool name + args. Here we mock it.
    """
    # If there's no pending tool, propose one:
    if not state.get("pending_tool"):
        state["pending_tool"] = {
            "tool_name": "add_numbers",
            "tool_args": {"a": 10, "b": 32},
            "rationale": "User asked for a sum (demo rationale).",
            "request_id": str(uuid.uuid4()),
        }
        return state

    # If we already executed and have a result, we could finish or propose next tool
    if state.get("last_tool_result") is not None:
        # End for demo
        return state

    return state


# -------------------------
# HITL Gate (interrupt)
# -------------------------
def hitl_gate_node(state: GraphState) -> GraphState:
    pending = state.get("pending_tool")
    if not pending:
        return state

    payload = {
        "type": "tool_approval",
        "request_id": pending["request_id"],
        "tool_name": pending["tool_name"],
        "tool_args": pending["tool_args"],
        "rationale": pending.get("rationale", ""),
        "options": ["approve", "revise", "cancel"],
    }

    # IMPORTANT: capture the resumed value here
    human_input = interrupt(payload)   # blocks until resume; then returns resume payload
    state["human_input"] = human_input
    return state


# -------------------------
# Router after HITL
# -------------------------
def after_hitl_router(state: GraphState) -> Literal["tool_executor", "cancel_handler"]:
    human = state.get("human_input") or {}
    decision = human.get("decision")
    if decision == "cancel":
        return "cancel_handler"
    return "tool_executor"


# -------------------------
# Tool Executor
# -------------------------
def tool_executor_node(state: GraphState) -> GraphState:
    pending = state.get("pending_tool") or {}
    human = state.get("human_input") or {}

    tool_name = pending.get("tool_name")
    tool_args = pending.get("tool_args") or {}

    decision = human.get("decision", "approve")

    if decision == "revise":
        tool_args = human.get("revised_args") or tool_args

    fn = TOOLS.get(tool_name)
    if not fn:
        state["last_tool_result"] = {"error": f"Unknown tool: {tool_name}"}
    else:
        state["last_tool_result"] = {
            "tool_name": tool_name,
            "tool_args": tool_args,
            "result": fn(**tool_args),
        }

    # Clear for next loop
    state["pending_tool"] = None
    state["human_input"] = None
    return state


def cancel_handler_node(state: GraphState) -> GraphState:
    pending = state.get("pending_tool") or {}
    state["last_tool_result"] = {
        "tool_name": pending.get("tool_name"),
        "tool_args": pending.get("tool_args"),
        "result": "CANCELLED_BY_HUMAN",
    }
    state["pending_tool"] = None
    state["human_input"] = None
    return state


def should_end(state: GraphState) -> bool:
    # demo end condition: once we have a last_tool_result, end
    return state.get("last_tool_result") is not None


def build_graph():
    """
    Checkpointing is the key to 'save state and resume later'.
    MemorySaver is fine for demos; for production use a durable store.
    """
    checkpointer = MemorySaver()

    g = StateGraph(GraphState)
    g.add_node("supervisor", supervisor_node)
    g.add_node("hitl_gate", hitl_gate_node)
    g.add_node("tool_executor", tool_executor_node)
    g.add_node("cancel_handler", cancel_handler_node)

    g.set_entry_point("supervisor")

    # Supervisor always goes to HITL gate before any tool can run
    g.add_edge("supervisor", "hitl_gate")

    # After HITL gate, route based on human decision
    g.add_conditional_edges("hitl_gate", after_hitl_router)

    # After tool/cancel, go back through supervisor (or end)
    g.add_edge("tool_executor", "supervisor")
    g.add_edge("cancel_handler", "supervisor")

    # Stop when condition met (demo)
    g.add_conditional_edges(
        "supervisor",
        lambda s: END if should_end(s) else "hitl_gate",
        {"hitl_gate": "hitl_gate", END: END},
    )

    return g.compile(checkpointer=checkpointer)
