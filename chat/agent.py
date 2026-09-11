from .tools import get_my_tasks, add_task, delete_task

SYSTEM_PROMPT = '''
You are Smart Student Assistant.
You help the authenticated user manage study tasks.
You must use tools for database actions.
Never invent database results.
Never access the database with raw SQL.
Respect the user's permissions.
Deletion must require explicit confirmation.
Keep answers short and clear.
'''

def run_agent(user, message):
    # Learning placeholder:
    # 1) Send SYSTEM_PROMPT + user message to the chosen LLM.
    # 2) Let the model select one of the Python tools.
    # 3) Validate tool arguments.
    # 4) Execute the tool with the authenticated user.
    # 5) Send the tool result back to the model for a final response.
    return {
        "message": "Agent layer is ready. Connect your training LLM here.",
        "available_tools": ["get_my_tasks", "add_task", "delete_task"],
    }
