# tools.py

from typing import Any, Dict



def add_numbers(a: int, b: int) -> int:
    return a + b

def echo_text(text: str) -> str:
    return f"You said: {text}"

TOOLS = {
    "add_numbers": add_numbers,
    "echo_text": echo_text,
}
