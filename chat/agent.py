import json
from google.genai import types
from .tools import add_task, delete_task, get_my_tasks

SYSTEM_PROMPT = """You are Smart Student Assistant for the authenticated user.
Use only the provided database context and tool results. Never invent records.
Use a tool for task actions; never write SQL or ORM queries yourself.
You may list the user's tasks, add a task, or request deletion of a task.
Keep responses short and clear. Never claim an action succeeded without its tool result.
"""

TOOL_DECLARATIONS = [
    types.FunctionDeclaration(
        name="get_my_tasks",
        description="List all tasks owned by the authenticated user.",
        parameters=types.Schema(type="OBJECT", properties={}),
    ),
    types.FunctionDeclaration(
        name="add_task",
        description="Create a task for the authenticated user.",
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "title": types.Schema(type="STRING", description="Task title."),
                "description": types.Schema(type="STRING", description="Optional task description."),
                "due_date": types.Schema(type="STRING", description="Optional YYYY-MM-DD due date."),
                "priority": types.Schema(type="STRING", description="low, medium, or high."),
            },
            required=["title"],
        ),
    ),
    types.FunctionDeclaration(
        name="delete_task",
        description="Delete one task owned by the authenticated user after confirmation.",
        parameters=types.Schema(
            type="OBJECT",
            properties={"task_id": types.Schema(type="INTEGER", description="The task ID.")},
            required=["task_id"],
        ),
    ),
]


def _tool_result(user, function_call):
    name = function_call.name
    arguments = dict(function_call.args or {})
    if name == "get_my_tasks":
        return get_my_tasks(user)
    if name == "add_task":
        task = add_task(user, **arguments)
        return {"created": True, "id": task.id, "title": task.title}
    if name == "delete_task":
        return delete_task(user, **arguments)
    raise ValueError("The model requested an unknown tool.")


def format_tool_result(client, tool_name, result):
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=(
            f"{SYSTEM_PROMPT}\n"
            f"The {tool_name} tool has completed.\n"
            f"Tool result: {json.dumps(result, default=str)}\n"
            "Respond naturally and briefly to the user. Do not claim anything beyond this result."
        ),
    )
    return response.text.strip()


def run_agent(user, message, user_context, client):
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part(
                    text=(
                        f"{SYSTEM_PROMPT}\n\nDATABASE CONTEXT:\n{user_context}"
                        f"\n\nUSER MESSAGE:\n{message}"
                    )
                )
            ],
        )
    ]
    tool_config = types.GenerateContentConfig(
        tools=[types.Tool(function_declarations=TOOL_DECLARATIONS)]
    )
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=contents,
        config=tool_config,
    )
    function_call = next(
        (part.function_call for part in response.candidates[0].content.parts if part.function_call),
        None,
    )
    if not function_call:
        return {"reply": response.text.strip(), "pending_delete": None}

    if function_call.name == "delete_task":
        return {
            "reply": "Are you sure you want to delete this task?",
            "pending_delete": function_call.args.get("task_id"),
        }

    result = _tool_result(user, function_call)
    follow_up = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=contents
        + [
            response.candidates[0].content,
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        function_response=types.FunctionResponse(
                            name=function_call.name,
                            response={"result": result},
                        )
                    )
                ],
            ),
        ],
        config=tool_config,
    )
    return {"reply": follow_up.text.strip(), "pending_delete": None}


    