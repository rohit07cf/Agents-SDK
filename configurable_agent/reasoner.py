# reasoner.py
import json
from typing import Any, Dict, List

from openai import AsyncOpenAI
from reasoning_prompt import build_reasoning_prompt

client = AsyncOpenAI()


async def call_reasoner(
    *,
    current_agent: str,
    agents_and_tools: Dict[str, List[str]],
    previous_tool_calls: List[Dict[str, Any]],
    input_message: str,
    model: str = "gpt-4.1-mini",
) -> Dict[str, Any]:
    """
    Call the LLM with the big ReAct reasoning prompt and return a parsed JSON plan.

    Returns one of:
      {"type": "tool", "tool_name": "...", "arguments": {...}}
      {"type": "transfer", "target_agent": "...", "reason": "..."}
      {"type": "final", "answer": "..."}
    """
    system_prompt = build_reasoning_prompt(
        current_agent=current_agent,
        agents_and_tools=agents_and_tools,
        previous_tool_calls=previous_tool_calls,
        input_message=input_message,
    )

    response = await client.responses.parse(
        model=model,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input_message},
        ],
    )

    # Adapt this extractor if your openai version differs slightly
    content = response.output[0].content[0].text  # type: ignore[attr-defined]
    plan = json.loads(content)
    return plan