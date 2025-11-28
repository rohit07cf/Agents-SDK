# sdk_agents.py (child agents – unchanged idea)

from agents import Agent
from hooks import MyAgentHooks
from tools import reasoning_step, add_numbers, subtract_numbers, multiply_numbers, echo_text, reverse_text, classify_intent, detect_sentiment
from models import SupervisorOutput

DEFAULT_MODEL = "gpt-4.1-mini"



echo_agent = Agent(
    name="EchoAgent",
    instructions=(
        "You are an echo-style agent.\n"
        "For each text-manipulation subtask, follow REASON → ACT:\n"
        "  1) REASON: call reasoning_step(thought=...) describing whether you will echo or reverse.\n"
        "  2) ACT: call reverse_text if asked to reverse/backwards, otherwise call echo_text.\n"
        "If there are other subtasks (like math), ONLY handle the echo/reverse part."
    ),
    tools=[reasoning_step, echo_text, reverse_text],
    model=DEFAULT_MODEL,
    hooks=MyAgentHooks(),
)

math_agent = Agent(
    name="MathAgent",
    instructions=(
        "You are a math specialist. Use REASON → ACT for each math operation and call one of "
        "add_numbers, subtract_numbers, multiply_numbers."
    ),
    tools=[reasoning_step, add_numbers, subtract_numbers, multiply_numbers],
    model=DEFAULT_MODEL,
    hooks=MyAgentHooks(),
)

simple_agent = Agent(
    name="SimpleAgent",
    instructions=(
        "Handle very simple add-or-echo queries using REASON → ACT with add_numbers or echo_text."
    ),
    tools=[reasoning_step, add_numbers, echo_text],
    model=DEFAULT_MODEL,
    hooks=MyAgentHooks(),
)

classifier_agent = Agent(
    name="ClassifierAgent",
    instructions=(
        "Classify intent and sentiment using REASON → ACT, then classify_intent and detect_sentiment."
    ),
    tools=[reasoning_step, classify_intent, detect_sentiment],
    model=DEFAULT_MODEL,
    hooks=MyAgentHooks(),
)


# 👇 NEW: Supervisor as MANAGER using agents-as-tools
supervisor_agent = Agent[SupervisorOutput](
    name="Supervisor",
     instructions=(
        "You are the Supervisor Agent for a multi-agent system.\n\n"
        "You NEVER solve subtasks yourself. Instead you orchestrate:\n"
        "  - run_simple_agent  -> SimpleAgent\n"
        "  - run_math_agent    -> MathAgent\n"
        "  - run_echo_agent    -> EchoAgent\n"
        "  - run_classifier_agent -> ClassifierAgent\n\n"
        "Follow a REASON → ACT loop for each subtask:\n"
        "  1) Call reasoning_step(thought=...) to explain what you’ll do.\n"
        "  2) Call ONE of the agent tools with an appropriate input.\n\n"
        "When you are completely done with all subtasks, you MUST return a "
        "structured output of type SupervisorOutput with:\n"
        "  - final_answer: a concise answer for the user that covers ALL subtasks.\n"
        "  - subtasks: a list where each item has:\n"
        "      * subtask: a short description (e.g. 'reverse TIHOR').\n"
        "      * agent: which child agent you used.\n"
        "      * result: the result returned by that agent.\n"
        "Do not return plain text as final output; always fill the SupervisorOutput object."
    ),
    # 🔑 CHILD AGENTS EXPOSED AS TOOLS HERE
    tools=[
        reasoning_step,
        simple_agent.as_tool(
            tool_name="run_simple_agent",
            tool_description="Use this to delegate simple add/echo tasks to SimpleAgent.",
        ),
        math_agent.as_tool(
            tool_name="run_math_agent",
            tool_description="Use this for any arithmetic involving numbers or math reasoning.",
        ),
        echo_agent.as_tool(
            tool_name="run_echo_agent",
            tool_description="Use this for reversing or echoing text.",
        ),
        classifier_agent.as_tool(
            tool_name="run_classifier_agent",
            tool_description="Use this for intent and sentiment classification.",
        ),
    ],
    model=DEFAULT_MODEL,
    hooks=MyAgentHooks(),
    output_type=SupervisorOutput,  # 👈 THIS is the structured-output wiring
)