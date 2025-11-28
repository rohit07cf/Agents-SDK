# tools.py
from typing import Any, Dict


def add_numbers(a: int, b: int) -> int:
    return a + b

def subtract_numbers(a: int, b: int) -> int:
    return a - b

def multiply_numbers(a: int, b: int) -> int:
    return a * b


def echo_text(text: str) -> str:
    return f"You said: {text}"

def reverse_text(text: str) -> str:
    return text[::-1]


# Very simple heuristic “ML-ish” tools for now
def classify_intent(text: str) -> str:
    lowered = text.lower()
    if any(w in lowered for w in ["add", "sum", "plus", "calculate"]):
        return "math_request"
    if any(w in lowered for w in ["repeat", "echo", "say back", "parrot"]):
        return "echo_request"
    if any(w in lowered for w in ["feeling", "mood", "happy", "sad"]):
        return "emotion_description"
    return "general_query"


def detect_sentiment(text: str) -> str:
    lowered = text.lower()
    if any(w in lowered for w in ["love", "great", "awesome", "good", "happy"]):
        return "positive"
    if any(w in lowered for w in ["hate", "bad", "terrible", "sad", "angry"]):
        return "negative"
    return "neutral"


TOOLS = {
    "add_numbers": add_numbers,
    "subtract_numbers": subtract_numbers,
    "multiply_numbers": multiply_numbers,
    "echo_text": echo_text,
    "reverse_text": reverse_text,
    "classify_intent": classify_intent,
    "detect_sentiment": detect_sentiment,
}