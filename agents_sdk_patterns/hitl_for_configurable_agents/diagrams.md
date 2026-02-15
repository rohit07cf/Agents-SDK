# HITL Architecture Diagrams

## 1. Tool-Call HITL Flow (Sync)

```
  Agent decides to call tool
         |
         v
  +------------------+
  | HITLPolicy       |    Checks: does this tool need approval?
  | .evaluate()      |    Looks up tool_name in config rules
  +--------+---------+
           |
      needs_approval?
      /            \
    NO              YES
     |               |
     v               v
  Execute        +------------------+
  tool           | request_human    |    The HITL tool
  directly       | _approval()     |    Routes by mode
                 +--------+---------+
                          |
                 +--------+---------+
                 | Human reviews:   |
                 | - approve        |
                 | - deny           |
                 | - edit args      |
                 +--------+---------+
                          |
                   ApprovalDecision
                   (Pydantic validated)
                          |
                  approved?
                  /        \
                YES         NO
                 |           |
                 v           v
              Execute     Return denial
              tool        to agent
              (maybe      (agent adjusts)
              with edits)
```

- **Policy check is the first gate** -- most tools pass through without HITL overhead
- **ApprovalRequest + ApprovalDecision** are Pydantic models -- fully typed, serializable
- **Edited args** flow back into the tool call, so humans can fix mistakes before execution
- **Denial is safe** -- agent gets structured feedback and can choose an alternative
- **Every path produces an audit trail** -- decision is logged regardless of outcome

## 2. Async Queue Flow

```
  Agent                          Store                        Approver
    |                              |                              |
    |  1. save_request(req)        |                              |
    |----------------------------->|                              |
    |                              |                              |
    |  2. poll for decision...     |                              |
    |  ........................    |                              |
    |                              |  3. list_pending()           |
    |                              |<-----------------------------|
    |                              |                              |
    |                              |  4. reviews request          |
    |                              |                              |
    |                              |  5. save_decision(dec)       |
    |                              |<-----------------------------|
    |                              |                              |
    |  6. get_decision() -> found! |                              |
    |<-----------------------------|                              |
    |                              |                              |
    |  7. execute tool             |                              |
    |  (or handle denial)          |                              |
```

- **Agent and approver are decoupled** -- they communicate only through the store
- **Polling is simple** but could be replaced with webhooks/callbacks in production
- **Timeout is a first-class concept** -- if no decision arrives, status="timeout" (safe deny)
- **Store can be in-memory (tests), file-based (demo), or a real DB/queue (production)**
- **The approver can be a human, a Slack bot, an approval service, or another agent**

## 3. Three Modes at a Glance

```
  sync_cli:
  Agent ---> [terminal prompt] ---> Human types ---> Decision ---> Execute
             (blocking)

  async_queue:
  Agent ---> [store] ---> [poll] ... [approver writes decision] ---> Execute
             (non-blocking, timeout possible)

  auto_rules:
  Agent ---> [rule engine] ---> low=approve / high=deny / med=check conditions
             (no human, instant)
```

- **sync_cli** = simplest, great for local dev and debugging
- **async_queue** = production-like, supports external approvers
- **auto_rules** = useful for dev/staging or known-safe patterns with audit logging
