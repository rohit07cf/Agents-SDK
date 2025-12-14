# start_workflow.py
import asyncio

from temporalio.client import Client

from workflows import AgenticOrchestrationWorkflow
from models import SupervisorOutput

TASK_QUEUE = "AGENTIC_AGENT_WORKFLOWS"


async def main():
    client = await Client.connect("localhost:7233")

    user_message = (
        "Whats the sentiments for: 'I am disappointed with the service provided'. "
        "Reverse the string '!EMOSEWA SI TIHOR'. Also multiply 2 and 3."
    )

    result: SupervisorOutput = await client.execute_workflow(
        AgenticOrchestrationWorkflow.run,
        user_message,
        id="agentic-workflow-001",
        task_queue=TASK_QUEUE,
    )

    print("\n🏁 FINAL OUTPUT FROM TEMPORAL WORKFLOW:")
    print("Final answer:", result.final_answer)
    print("\nSubtasks:")
    for st in result.subtasks:
        print(f"- [{st.agent}] {st.subtask}: {st.result}")


if __name__ == "__main__":
    asyncio.run(main())
