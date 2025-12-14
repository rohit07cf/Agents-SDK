# reasoner.py
from typing import Any, Dict, List
from openai import AsyncOpenAI
from reasoning_prompt import build_reasoning_prompt


async def call_reasoner(
    *,
    current_agent: str,
    agents_and_tools: Dict[str, List[str]],
    previous_tool_calls: List[Dict[str, Any]],
    input_message: str,
    model: str = "gpt-4.1-mini",
) -> Dict[str, Any]:
    """
    Call the LLM with the big ReAct reasoning prompt and return parsed plan.
    OpenAI client is created lazily inside the activity, not at import time.
    """
    client = AsyncOpenAI()  # ✅ now inside function, safe for activities

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

    # parse() already returns structured output; adapt if needed
    return response.output
