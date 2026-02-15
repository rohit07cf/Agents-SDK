# Handoffs vs Agents-as-Tools

## What We Are Building

- Two runnable examples showing the two core multi-agent orchestration patterns
- Config-driven agent creation using Pydantic (same pattern as `configurable_agent/`)
- Hierarchical agent trees (AgentTree + AgentNode) with ASCII visualization

Both patterns answer the same question:
**"How does a supervisor agent delegate work to a child agent?"**

---

## Key Definitions

### Tool Call
- A **function invocation** within an agent's reasoning loop
- The agent calls a function, gets a return value, and keeps going
- The agent **never loses control**

### Handoff (OpenAI Agents SDK)
- A **transfer of control** from one agent to another
- The source agent **pauses**; the target agent **takes over**
- When the target finishes, control returns to the source
- The SDK uses `handoff()` to express this

### Agent-as-Tool
- A child agent is **wrapped as a tool** using `.as_tool()`
- The parent calls it like any other function tool
- The parent **never loses control** -- the child is just a function call
- Pattern used in `configurable_agent/sdk_agents.py`

---

## ELI10 Analogies

### Handoff: Principal and Teacher

> The **principal** (supervisor) has a student who needs math help.
> The principal **sends the student to the math teacher**.
> The math teacher **takes full control** of the lesson.
> When the lesson is done, the student **goes back to the principal**
> with a report card (HandoffResult).
>
> The principal **stopped doing work** while the teacher had the student.

- **Control ownership**: transferred to the teacher
- **State ownership**: the teacher owns the conversation
- **Principal resumes** only after the teacher is done

### Agent-as-Tool: Chef and Blender

> The **chef** (supervisor) is making a smoothie.
> The chef puts ingredients in the **blender** (child agent) and presses the button.
> The blender does its job and **returns blended result**.
> The chef **never stopped cooking** -- the blender is just a tool.
>
> The chef decides what to do with the blended output.

- **Control ownership**: always with the chef
- **State ownership**: chef owns the full recipe state
- **Blender is stateless**: input in, output out

---

## How to Run

```bash
cd agents_sdk_patterns/handoffs_vs_agents_as_tools

# Handoff pattern
python 01_handoff_example.py

# Agent-as-tool pattern
python 02_agent_as_tool_example.py
```

No API key needed -- examples use local simulation to demonstrate the patterns.

---

## Interview-Ready Answers

### 30-Second Answer

> "In the OpenAI Agents SDK, there are two ways a supervisor delegates to a child agent.
> **Handoff** transfers full control -- the supervisor pauses, the child takes over,
> and returns a result when done. **Agent-as-tool** keeps the supervisor in control --
> the child agent is called as a bounded function, like any other tool.
> Use handoff for complex multi-step specialist tasks.
> Use agent-as-tool for quick, bounded lookups."

### 2-Minute Answer

> "Both patterns solve the same problem: a supervisor needs help from a specialist.
>
> With **handoff**, the supervisor explicitly transfers control to the specialist.
> The specialist now owns the conversation -- it can do multi-step reasoning,
> call its own tools, and take as long as needed. When it finishes, it returns
> a structured result (HandoffResult) and the supervisor resumes. This is great
> for complex tasks where the specialist needs autonomy -- like a research agent
> that needs to search, read, and synthesize.
>
> With **agent-as-tool**, the supervisor wraps the specialist as a tool using
> `.as_tool()`. When the supervisor calls this tool, the specialist runs as a
> bounded function: input in, output out. The supervisor never loses control.
> This is ideal for quick classifications, lookups, or transformations.
>
> The key difference is **who owns control and state**. In handoff, the child
> owns both temporarily. In agent-as-tool, the parent owns both always.
>
> In our codebase, `configurable_agent/sdk_agents.py` uses the agent-as-tool
> pattern: the Supervisor calls `math_agent.as_tool(...)` and
> `echo_agent.as_tool(...)`. If we wanted the Supervisor to fully hand off
> to a research agent, we'd use `handoff()` instead.
>
> Both patterns produce validated Pydantic outputs -- HandoffResult for handoffs,
> ToolResponse for agent-as-tool -- so the supervisor always gets structured data."

---

## File Map

| File | Purpose |
|------|---------|
| `schemas.py` | Pydantic configs (ModelConfig, AgentConfig, TreeConfig) + output contracts (HandoffResult, ToolResponse) |
| `configurable_agent_factory.py` | Factory: build Agent instances from AgentConfig |
| `agent_tree/` | AgentNode + AgentTree with ASCII visualization |
| `01_handoff_example.py` | Runnable handoff pattern demo |
| `02_agent_as_tool_example.py` | Runnable agent-as-tool pattern demo |
| `comparison.md` | Side-by-side comparison table |
| `diagrams.md` | ASCII flow diagrams |

---

## TL;DR (Interview Summary)

- **Handoff** = transfer control to child. Child takes over. Supervisor pauses.
- **Agent-as-Tool** = call child as a function. Supervisor keeps control.
- Handoff is for **complex, multi-step specialist tasks** (research, planning)
- Agent-as-tool is for **bounded, quick operations** (classify, lookup, transform)
- Both use **Pydantic configs** as the source of truth for agent creation
- Both return **validated structured outputs** (HandoffResult / ToolResponse)
- **Control ownership** is the key differentiator
- In `configurable_agent/sdk_agents.py`, the Supervisor uses the **agent-as-tool** pattern via `.as_tool()`
