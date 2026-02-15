# HITL (Human-in-the-Loop) for Configurable Agents

## What is HITL?

- A pattern where an AI agent **pauses before risky actions** and asks a human to approve, deny, or edit
- The human acts as a **safety gate** between the agent's decision and actual execution
- Everything flows through a **structured tool call**, not ad-hoc prompts

## Why Tool-Based HITL is Clean

- **Control**: the HITL check is an explicit step in the agent's tool pipeline, not a side-channel
- **Audit**: every request + decision is a Pydantic model, logged and traceable
- **Composability**: plug HITL into any tool by adding a rule -- no code changes in the tool itself
- **Testability**: mock the input function, test policies in isolation, validate contracts

## How It Works End-to-End

```
1. Agent decides to call a tool (e.g., send_email)
2. execute_tool_with_hitl() intercepts the call
3. HITLPolicy checks: does this tool need approval?
4. If NO  -> tool executes directly
5. If YES -> build ApprovalRequest (Pydantic)
6. request_human_approval tool routes by mode:
     - sync_cli:    prompt human in terminal
     - async_queue: write to store, poll for decision
     - auto_rules:  auto-approve/deny by risk level
7. Human (or auto-rule) returns ApprovalDecision
8. If APPROVED  -> execute tool (with optional edited args)
9. If DENIED    -> agent gets denial, must adjust
10. Result + decision logged
```

## How It Integrates with Configurable Agents

- Agents are built from `AgentConfig` (Pydantic) -- same pattern as `configurable_agent/sdk_agents.py`
- HITL config is a separate `HITLConfig` attached at the execution layer
- The factory's `execute_tool_with_hitl()` wraps every tool call
- **Key idea**: HITL is a cross-cutting concern, not baked into individual tools

## ELI10 Analogy

> Imagine a junior employee (the agent) who drafts emails all day.
>
> Some emails are routine (low risk) -- they go out automatically.
> But emails to the CEO? Those are **high risk**.
>
> Before sending a high-risk email, the junior **puts it on the manager's desk**
> (the ApprovalRequest). The manager reads it and either:
> - **Stamps "APPROVED"** -- email gets sent
> - **Stamps "DENIED"** with a note -- email doesn't go out
> - **Edits the email** and stamps "APPROVED" -- corrected version goes out
>
> The junior doesn't send anything risky without that stamp.
> That's HITL.

- **Junior employee** = the agent
- **Manager's desk** = the approval store
- **Stamp** = the ApprovalDecision
- **Risk rules** = which emails need the manager vs. which go directly

## Common Interview Questions

**"What is Human-in-the-Loop in AI agents?"**
> A safety pattern where the agent requests human approval before
> executing risky or irreversible actions. The human can approve,
> deny, or modify the action. This prevents uncontrolled side effects.

**"How do you implement HITL without blocking the entire system?"**
> Use async queue mode: the agent writes a request to a store,
> then either polls or gets a callback when the human decides.
> The agent can do other work while waiting, or timeout safely.

**"How do you decide which actions need approval?"**
> A policy layer evaluates each tool call against configured rules.
> Rules map tool names to risk levels. High-risk = always approve.
> Low-risk = pass through. Medium = check conditions (auto_approve_if).

**"Why not just hardcode approval checks in each tool?"**
> That violates separation of concerns. The tool shouldn't know about
> approval workflows. HITL is a cross-cutting concern handled by a
> wrapper (execute_tool_with_hitl) that sits between agent and tool.

**"How do you test HITL?"**
> Inject a mock input function for sync_cli mode. Use InMemoryApprovalStore
> for async mode. Test policies in isolation with unit tests. All contracts
> are Pydantic-validated, so invalid data fails fast.

## How to Run

```bash
cd agents_sdk_patterns/hitl_for_configurable_agents

# Example 1: Sync CLI (interactive terminal approval)
python examples/01_sync_cli_approval.py

# Example 2: Async queue (background approver thread)
python examples/02_async_queue_approval.py

# Example 3: Auto-approval rules (no human needed)
python examples/03_auto_approval_rules.py

# Tests
python -m pytest tests/ -v
```

No API key needed -- all examples use local simulation.

## File Map

| File | Purpose |
|------|---------|
| `schemas.py` | Pydantic configs (HITLConfig, HITLRule, AgentConfig) + contracts (ApprovalRequest, ApprovalDecision) |
| `hitl_policy.py` | Policy layer: evaluates whether a tool call needs approval |
| `hitl_tool.py` | The `request_human_approval` tool (sync_cli / async_queue / auto_rules) |
| `approval_store.py` | Persistence: InMemoryApprovalStore + FileApprovalStore |
| `configurable_agent_factory.py` | Agent factory + `execute_tool_with_hitl()` wrapper |
| `examples/01_sync_cli_approval.py` | Interactive terminal approval demo |
| `examples/02_async_queue_approval.py` | Async queue with background approver |
| `examples/03_auto_approval_rules.py` | Risk-based auto-approve/deny demo |
| `tests/test_hitl_tool.py` | Unit tests for policy, store, tool, and edited args |
| `diagrams.md` | ASCII architecture diagrams |

## TL;DR (Interview Summary)

- HITL is a **safety gate** between agent decisions and tool execution
- Implemented as a **tool** the agent calls (`request_human_approval`)
- Three modes: **sync CLI** (terminal), **async queue** (store + poll), **auto rules** (risk-based)
- All configs are **Pydantic models** (HITLConfig, HITLRule) -- validated, serializable
- A **policy layer** decides which tools need approval based on risk_level rules
- Humans can **approve, deny, or edit tool args** before execution
- The pattern is **pluggable**: add a rule to any tool without changing the tool's code
- Follows the same **config-driven agent creation** pattern as `configurable_agent/`
