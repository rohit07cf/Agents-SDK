# tools.py
from agents import function_tool
from hooks import reasoning_hooks

@function_tool
async def reasoning_step(thought: str) -> str:
    """
    Record a reasoning step as part of the REASON phase in a ReAct loop.

    LLM usage pattern:
    - Before calling any other tool (ACT), call reasoning_step with a short
      description of what you're about to do and why.
    """
    await reasoning_hooks.on_reasoning_step(thought)
    # The return value isn't important; it's just to satisfy the tool contract.
    return "Reasoning recorded."

@function_tool
def add_numbers(a: int, b: int) -> int:
    """Add two integers and return the sum."""
    return a + b


@function_tool
def subtract_numbers(a: int, b: int) -> int:
    """Subtract b from a and return the result."""
    return a - b


@function_tool
def multiply_numbers(a: int, b: int) -> int:
    """Multiply two integers and return the product."""
    return a * b


@function_tool
def echo_text(text: str) -> str:
    """Return the text back to the user."""
    return f"You said: {text}"


@function_tool
def reverse_text(text: str) -> str:
    """Return the text reversed."""
    return text[::-1]


@function_tool
def classify_intent(text: str) -> str:
    """
    Heuristic intent classifier: returns labels like
    'math_request', 'echo_request', 'emotion_description', 'general_query'.
    """
    lowered = text.lower()
    if any(w in lowered for w in ["add", "sum", "plus", "calculate", "number"]):
        return "math_request"
    if any(w in lowered for w in ["repeat", "echo", "say back", "parrot"]):
        return "echo_request"
    if any(w in lowered for w in ["feeling", "mood", "happy", "sad", "angry"]):
        return "emotion_description"
    return "general_query"


@function_tool
def detect_sentiment(text: str) -> str:
    """
    Very simple sentiment detector: 'positive', 'negative', or 'neutral'.
    """
    lowered = text.lower()
    if any(w in lowered for w in ["love", "great", "awesome", "good", "happy", "fantastic"]):
        return "positive"
    if any(w in lowered for w in ["hate", "bad", "terrible", "awful", "sad", "angry"]):
        return "negative"
    return "neutral"
