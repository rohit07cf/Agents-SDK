# models.py
from typing import List
from pydantic import BaseModel

class SubtaskResult(BaseModel):
    subtask: str          # e.g. "reverse_text", "multiply_numbers"
    agent: str            # e.g. "EchoAgent", "MathAgent"
    result: str           # human-readable or serialized result

class SupervisorOutput(BaseModel):
    final_answer: str     # what you actually show to the user
    subtasks: List[SubtaskResult]
