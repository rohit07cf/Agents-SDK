# worker.py
import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from workflows import AgenticOrchestrationWorkflow
from activities import planner_activity, orchestrator_activity

TASK_QUEUE = "AGENTIC_AGENT_WORKFLOWS"


async def main():
    client = await Client.connect("localhost:7233")

    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[AgenticOrchestrationWorkflow],
        activities=[planner_activity, orchestrator_activity],
    )

    print("🚀 Temporal Worker started, listening on task queue:", TASK_QUEUE)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
