# Handoff vs Agent-as-Tool: Comparison

## Side-by-Side

| Feature | Handoff | Agent-as-Tool |
|---------|---------|---------------|
| **Who owns control?** | Child agent (temporarily) | Parent agent (always) |
| **Who owns state?** | Child agent (during execution) | Parent agent (always) |
| **When to use?** | Complex multi-step specialist tasks | Quick bounded operations |
| **Multi-step orchestration** | Child can do multi-step reasoning | Single input -> output call |
| **Failure isolation** | Child failure = handoff failure, parent must handle | Tool failure = one failed call, parent retries |
| **Mental model** | "Go talk to the specialist" | "Use this tool" |
| **SDK method** | `handoff()` | `agent.as_tool()` |
| **Child autonomy** | High -- child reasons independently | Low -- child is a function |
| **Parent during child execution** | Paused / waiting | Active / in control |
| **Output type** | HandoffResult | ToolResponse |
| **Conversation ownership** | Transfers to child | Stays with parent |
| **Analogy** | Principal sends you to the teacher | Chef uses a blender |

---

## Common Mistakes

- **Using handoff when agent-as-tool suffices**
  - If the child just does one thing (classify, lookup), use `.as_tool()`
  - Handoff adds overhead: context transfer, control transfer, return handling

- **Using agent-as-tool when the child needs multi-step reasoning**
  - If the child needs to call multiple tools, reason between them, and iterate, use handoff
  - Agent-as-tool forces a single bounded call

- **Confusing "tool call" with "handoff"**
  - A tool call is `agent -> function -> agent` (same agent)
  - A handoff is `agent_A -> agent_B -> agent_A` (different agents)

- **Forgetting to validate outputs**
  - Both patterns should return Pydantic-validated structured outputs
  - Don't pass raw strings between agents -- use HandoffResult / ToolResponse

---

## Decision Cheat Sheet

1. **Child needs 1 step?** -> Agent-as-tool
2. **Child needs multi-step reasoning?** -> Handoff
3. **Child needs its own tools + reasoning loop?** -> Handoff
4. **Parent needs to stay in control?** -> Agent-as-tool
5. **Multiple children called in sequence?** -> Agent-as-tool for each
6. **One child handles an entire subtask end-to-end?** -> Handoff

---

## If the Interviewer Asks...

**"What's the difference between handoff and agent-as-tool?"**
> "Handoff transfers control -- the child agent takes over and runs independently.
> Agent-as-tool keeps the parent in control -- the child is just a function call."

**"When would you choose handoff over agent-as-tool?"**
> "When the child agent needs to do multi-step reasoning with its own tools.
> For example, a research agent that needs to search, read multiple sources,
> and synthesize findings. That requires autonomy -- handoff gives it."

**"When would you choose agent-as-tool?"**
> "When the task is bounded and quick -- classify a message, look up a value,
> run a calculation. The parent stays in control and uses the result immediately."

**"Can you combine both patterns?"**
> "Yes. A supervisor can use agent-as-tool for quick lookups and handoff for
> complex subtasks in the same orchestration flow. The choice is per-delegation,
> not per-system."

**"How does the OpenAI Agents SDK implement these?"**
> "Agent-as-tool uses `.as_tool()` on the child agent -- it wraps the agent
> as a callable function tool. Handoff uses the `handoff()` function which
> transfers conversation control to the target agent."
