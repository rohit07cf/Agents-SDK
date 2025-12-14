from typing import Any, Dict

def add_numbers(a: float, b: float) -> float:
    return a + b

def echo_text(text: str) -> str:
    return text

TOOLS: Dict[str, Any] = {
    "add_numbers": add_numbers,
    "echo_text": echo_text,
}