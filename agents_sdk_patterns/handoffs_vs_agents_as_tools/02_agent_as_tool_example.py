"""
02_agent_as_tool_example.py - Demonstrates the AGENT-AS-TOOL pattern.

AGENT-AS-TOOL = the parent agent stays in control and calls the
child agent as a bounded tool function. The child runs, returns
a result, and the parent continues reasoning.

Key difference from handoff:
  - The PARENT keeps control at all times
  - The child is just a function call (like using a blender)
  - No state transfer, no conversation ownership change

Think of it like: a chef uses a blender. The blender does its
job (blend), returns the result, and the chef continues cooking.
The chef never stops being the chef.

Run:
    cd agents_sdk_patterns/handoffs_vs_agents_as_tools
    python 02_agent_as_tool_example.py
"""

import asyncio
import sys
import os

# Ensure local imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from schemas import (
    AgentConfig,
    ModelConfig,
    PromptConfig,
    ToolResponse,
    TreeConfig,
)
from configurable_agent_factory import (
    Agent,
    create_agent_from_config,
    register_tool,
)
from agent_tree import AgentTree


# ── Step 1: Define tools ────────────────────────────────────────────


def analyze_sentiment(text: str) -> str:
    """Simple sentiment analysis."""
    lowered = text.lower()
    if any(w in lowered for w in ["love", "great", "awesome", "good", "happy"]):
        return "positive"
    if any(w in lowered for w in ["hate", "bad", "terrible", "awful", "sad"]):
        return "negative"
    return "neutral"


def classify_intent(text: str) -> str:
    """Classify user intent."""
    lowered = text.lower()
    if any(w in lowered for w in ["buy", "purchase", "order"]):
        return "purchase_intent"
    if any(w in lowered for w in ["help", "support", "issue", "problem"]):
        return "support_request"
    if any(w in lowered for w in ["info", "tell", "what", "how"]):
        return "information_request"
    return "general"


# Register tools
register_tool("analyze_sentiment", analyze_sentiment)
register_tool("classify_intent", classify_intent)


# ── Step 2: Build configs (Pydantic) ───────────────────────────────

tree_config = TreeConfig(
    supervisor=AgentConfig(
        name="OrchestratorAgent",
        role="supervisor",
        model_config=ModelConfig(model_name="gpt-4.1-mini", temperature=0.0),
        prompt_config=PromptConfig(
            system_template=(
                "You are an orchestrator agent. "
                "You stay in control. Use ClassifierAgent as a TOOL "
                "to classify and analyze user messages, then decide "
                "the final response yourself."
            ),
        ),
        tools=[],  # child agents will be wired as tools
        handoff_targets=[],  # no handoffs - this is agent-as-tool
    ),
    children=[
        AgentConfig(
            name="ClassifierAgent",
            role="tool-agent",
            model_config=ModelConfig(model_name="gpt-4.1-mini"),
            prompt_config=PromptConfig(
                system_template="You classify text by sentiment and intent.",
            ),
            tools=["analyze_sentiment", "classify_intent"],
        ),
    ],
)


# ── Step 3: Build agents from config ───────────────────────────────

orchestrator = create_agent_from_config(tree_config.supervisor)
classifier_agent = create_agent_from_config(tree_config.children[0])

# Wire child agent AS A TOOL on the parent
# This is the same pattern as sdk_agents.py:
#   classifier_agent.as_tool(tool_name="run_classifier_agent", ...)
classifier_tool = classifier_agent.as_tool(
    tool_name="run_classifier_agent",
    tool_description="Classify user message by sentiment and intent.",
)
orchestrator.tools.append(classifier_tool)
orchestrator._tool_map["run_classifier_agent"] = classifier_tool


# ── Step 4: Build + visualize the AgentTree ─────────────────────────

agents_map = {
    orchestrator.name: orchestrator,
    classifier_agent.name: classifier_agent,
}

tree = AgentTree.build_from_config(tree_config, agents=agents_map)


# ── Step 5: Run the agent-as-tool simulation ────────────────────────


async def run_agent_as_tool(user_message: str) -> ToolResponse:
    """
    Simulate the agent-as-tool pattern end-to-end.

    Flow:
      1. OrchestratorAgent receives user message
      2. Orchestrator calls ClassifierAgent AS A TOOL
      3. ClassifierAgent runs its tools, returns result
      4. Orchestrator receives ToolResponse, continues reasoning
      5. Orchestrator produces final output
    """

    print("=" * 60)
    print("AGENT-AS-TOOL PATTERN - Execution Trace")
    print("=" * 60)

    # -- Orchestrator start --
    print(f"\n[1] OrchestratorAgent starts (and KEEPS control)")
    print(f"    Input: {user_message!r}")
    print(f"    Note: Orchestrator stays in the driver's seat")

    # -- Tool invocation --
    # WHY this is agent-as-tool:
    #   - The orchestrator does NOT transfer control
    #   - ClassifierAgent runs as a bounded function call
    #   - Like calling a utility: input -> output, no state transfer
    print(f"\n[2] OrchestratorAgent invokes ClassifierAgent AS A TOOL")
    print(f"    WHY this is agent-as-tool:")
    print(f"      - Orchestrator does NOT pause or yield control")
    print(f"      - ClassifierAgent is called like a function")
    print(f"      - Parent waits for return value, then continues")

    # Run the child agent's tools directly
    sentiment = analyze_sentiment(user_message)
    intent = classify_intent(user_message)
    print(f"\n[3] ClassifierAgent executes (as a bounded tool)")
    print(f"    analyze_sentiment -> {sentiment!r}")
    print(f"    classify_intent   -> {intent!r}")

    # -- Build validated ToolResponse --
    tool_response = ToolResponse(
        tool_name="run_classifier_agent",
        result=f"sentiment={sentiment}, intent={intent}",
        metadata={
            "sentiment": sentiment,
            "intent": intent,
            "input_length": len(user_message),
        },
    )
    print(f"\n[4] ClassifierAgent returns ToolResponse (Pydantic-validated)")
    print(f"    tool_name: {tool_response.tool_name}")
    print(f"    result:    {tool_response.result}")
    print(f"    metadata:  {tool_response.metadata}")

    # -- Orchestrator continues --
    print(f"\n[5] OrchestratorAgent CONTINUES reasoning (never lost control)")
    print(f"    Decision: route to '{intent}' handler with '{sentiment}' tone")
    final = f"Routed to {intent} pipeline. Tone: {sentiment}."
    print(f"    Final output: {final}")

    print(f"\n{'=' * 60}")
    print(f"AGENT-AS-TOOL COMPLETE")
    print(f"{'=' * 60}")

    return tool_response


# ── Main ────────────────────────────────────────────────────────────

def main():
    print("\n")
    tree.visualize()
    print("\n")

    result = asyncio.run(
        run_agent_as_tool("I love this product! Can you tell me more about it?")
    )

    # Validate the result is a proper Pydantic model
    print(f"\n-- Pydantic validation --")
    print(f"   Type:  {type(result).__name__}")
    print(f"   JSON:  {result.model_dump_json(indent=2)}")
    print(f"   Valid: True (would raise ValidationError otherwise)")


if __name__ == "__main__":
    main()
