# Architecture Diagrams

## Handoff Pattern

```
  +------------------+
  |   Supervisor     |     1. Receives user query
  |   Agent          |     2. Decides: "I need a specialist"
  +--------+---------+     3. HANDS OFF control
           |
           | handoff() -- control TRANSFERS
           v
  +------------------+
  |   Specialist     |     4. Takes over fully
  |   Agent          |     5. Runs its own tools
  |                  |     6. Builds HandoffResult
  +--------+---------+
           |
           | return HandoffResult -- control RETURNS
           v
  +------------------+
  |   Supervisor     |     7. Resumes with result
  |   Agent          |     8. Synthesizes final answer
  +------------------+
```

- Supervisor **pauses** during step 4-6
- Specialist **owns** the conversation while executing
- Control flows: Supervisor -> Specialist -> Supervisor

---

## Agent-as-Tool Pattern

```
  +------------------+
  |   Supervisor     |     1. Receives user query
  |   Agent          |     2. Decides: "I need data from a child"
  |                  |     3. Calls child AS A TOOL
  |                  |          |
  |                  |          v
  |   +--------------+----+
  |   | Tool:        |    |    4. Child runs as bounded function
  |   | ChildAgent   |    |    5. Returns ToolResponse
  |   +--------------+----+
  |                  |          |
  |                  |     <----+
  |                  |     6. Supervisor continues reasoning
  |                  |     7. Returns final answer
  +------------------+
```

- Supervisor **never stops** -- child runs inside parent's loop
- Child is a **function call**, not a conversation takeover
- Control stays: Supervisor -> Supervisor (child is inline)

---

## Side-by-Side Flow

```
  HANDOFF                          AGENT-AS-TOOL
  --------                         ---------------

  Supervisor                       Supervisor
     |                                |
     | handoff()                      | tool_call()
     | (control transfers)            | (function call)
     v                                |
  Specialist                          v
     |                             ChildAgent (runs inline)
     | (runs independently)           |
     |                                | return ToolResponse
     | return HandoffResult           |
     v                                v
  Supervisor                       Supervisor
     |                                |
     | (resumes)                      | (continues -- never stopped)
     v                                v
  Final Answer                     Final Answer
```

- Left: two separate execution contexts
- Right: one continuous execution context

---

## Agent Tree (Both Examples)

```
  Handoff Example:              Agent-as-Tool Example:

  Supervisor                    OrchestratorAgent
  `-- ResearchAgent             `-- ClassifierAgent
      [research_topic]              [analyze_sentiment,
                                     classify_intent]
```

- Root = supervisor / orchestrator
- Children = specialist agents
- Tools listed per node

---

## Control Ownership Timeline

```
  Time -->

  HANDOFF:
  [Supervisor===]              [===Supervisor]
                 [==Specialist==]

  AGENT-AS-TOOL:
  [Supervisor==========tool()=========Supervisor]
                       [Child]
```

- Handoff: supervisor has a **gap** where it's not in control
- Agent-as-tool: supervisor has **continuous** control
