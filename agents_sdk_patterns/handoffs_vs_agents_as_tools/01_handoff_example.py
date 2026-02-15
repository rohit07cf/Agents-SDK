"""
01_handoff_example.py - Demonstrates the HANDOFF pattern.

HANDOFF = supervisor transfers FULL CONTROL to a child agent.
The child takes over, executes, and returns control + result
back to the supervisor.

Key difference from agent-as-tool:
  - The child OWNS the conversation while it runs
  - The supervisor PAUSES and WAITS
  - State is transferred, not just a function call

Think of it like: a school principal sends you to the math
teacher. The math teacher now runs the class. When done,
you go back to the principal with your grade.

Run:
    cd agents_sdk_patterns/handoffs_vs_agents_as_tools
    python 01_handoff_example.py
"""

import asyncio
import sys
import os

# Ensure local imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from schemas import (
    AgentConfig,
    HandoffResult,
    ModelConfig,
    PromptConfig,
    TreeConfig,
)
from configurable_agent_factory import (
    Agent,
    create_agent_from_config,
    register_tool,
)
from agent_tree import AgentTree


# ── Step 1: Define tools ────────────────────────────────────────────


def research_topic(query: str) -> str:
    """Simulate researching a topic (would call an API in production)."""
    return f"Research findings for '{query}': AI agents use LLMs to reason and act autonomously."


def summarize_text(text: str) -> str:
    """Produce a concise summary."""
    return f"Summary: {text[:80]}..."


# Register tools so the factory can resolve them by name
register_tool("research_topic", research_topic)
register_tool("summarize_text", summarize_text)


# ── Step 2: Build configs (Pydantic) ───────────────────────────────

tree_config = TreeConfig(
    supervisor=AgentConfig(
        name="Supervisor",
        role="supervisor",
        model_config=ModelConfig(model_name="gpt-4.1-mini", temperature=0.0),
        prompt_config=PromptConfig(
            system_template=(
                "You are a supervisor agent. "
                "When a research question arrives, HANDOFF to ResearchAgent. "
                "After the handoff returns, synthesize the final answer."
            ),
        ),
        tools=["summarize_text"],
        handoff_targets=["ResearchAgent"],
    ),
    children=[
        AgentConfig(
            name="ResearchAgent",
            role="specialist",
            model_config=ModelConfig(model_name="gpt-4.1-mini"),
            prompt_config=PromptConfig(
                system_template="You are a research specialist. Use research_topic to find information.",
            ),
            tools=["research_topic"],
        ),
    ],
)


# ── Step 3: Build agents from config ───────────────────────────────

supervisor = create_agent_from_config(tree_config.supervisor)
research_agent = create_agent_from_config(tree_config.children[0])


# ── Step 4: Build + visualize the AgentTree ─────────────────────────

agents_map = {
    supervisor.name: supervisor,
    research_agent.name: research_agent,
}

tree = AgentTree.build_from_config(tree_config, agents=agents_map)


# ── Step 5: Run the handoff simulation ──────────────────────────────


async def run_handoff(user_query: str) -> HandoffResult:
    """
    Simulate the handoff pattern end-to-end.

    Flow:
      1. Supervisor receives user query
      2. Supervisor decides to HANDOFF to ResearchAgent
      3. ResearchAgent takes full control, runs tools
      4. ResearchAgent returns HandoffResult
      5. Supervisor resumes, uses result
    """

    print("=" * 60)
    print("HANDOFF PATTERN - Execution Trace")
    print("=" * 60)

    # -- Supervisor start --
    print(f"\n[1] Supervisor starts")
    print(f"    Input: {user_query!r}")
    print(f"    Checking handoff targets: {tree_config.supervisor.handoff_targets}")

    # -- Handoff decision --
    target = tree_config.supervisor.handoff_targets[0]
    print(f"\n[2] Supervisor HANDS OFF control to '{target}'")
    print(f"    WHY this is a handoff:")
    print(f"      - Supervisor PAUSES execution")
    print(f"      - ResearchAgent TAKES OVER the conversation")
    print(f"      - Control is fully transferred, not just a tool call")

    # -- Child agent executes --
    print(f"\n[3] ResearchAgent executes (has full control)")
    child_result = await research_agent.run(user_query)
    research_output = child_result.get("research_topic", "no result")
    print(f"    Tool used: research_topic")
    print(f"    Raw result: {research_output}")

    # -- Build validated HandoffResult --
    handoff_result = HandoffResult(
        from_agent="ResearchAgent",
        to_agent="Supervisor",
        status="success",
        summary=research_output,
        payload={"query": user_query, "source": "research_topic"},
        artifacts=["research_findings_v1"],
    )
    print(f"\n[4] ResearchAgent returns HandoffResult (Pydantic-validated)")
    print(f"    status:    {handoff_result.status}")
    print(f"    summary:   {handoff_result.summary}")
    print(f"    artifacts: {handoff_result.artifacts}")

    # -- Supervisor resumes --
    print(f"\n[5] Supervisor RESUMES control")
    summary = summarize_text(handoff_result.summary)
    print(f"    Supervisor synthesizes: {summary}")

    print(f"\n{'=' * 60}")
    print(f"HANDOFF COMPLETE")
    print(f"{'=' * 60}")

    return handoff_result


# ── Main ────────────────────────────────────────────────────────────

def main():
    print("\n")
    tree.visualize()
    print("\n")

    result = asyncio.run(run_handoff("What are AI agents?"))

    # Validate the result is a proper Pydantic model
    print(f"\n-- Pydantic validation --")
    print(f"   Type:  {type(result).__name__}")
    print(f"   JSON:  {result.model_dump_json(indent=2)}")
    print(f"   Valid: True (would raise ValidationError otherwise)")


if __name__ == "__main__":
    main()
