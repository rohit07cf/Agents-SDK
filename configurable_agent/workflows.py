# workflows.py
from __future__ import annotations

from datetime import timedelta
from typing import Dict, Any

from temporalio import workflow

from models import SupervisorOutput


@workflow.defn
class AgenticOrchestrationWorkflow:
    """
    Temporal Workflow that orchestrates:
    1) planner_activity -> LLM planner
    2) orchestrator_activity -> Supervisor + child agents
    """

    @workflow.run
    async def run(self, user_message: str) -> SupervisorOutput:
        # 1) Planner activity
        plan: Dict[str, Any] = await workflow.execute_activity(
            "planner_activity",          # 👈 use the registered activity NAME
            user_message,
            schedule_to_close_timeout=timedelta(seconds=60),
        )

        # 2) Orchestrator activity
        result: SupervisorOutput = await workflow.execute_activity(
            "orchestrator_activity",     # 👈 name, not function ref
            user_message,
            plan,
            schedule_to_close_timeout=timedelta(seconds=120),
        )

        return result
