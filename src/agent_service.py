import json
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from groq import Groq

from .todo_service import TodoService
from .entities import Task, TaskType, TaskStatus

load_dotenv()

# Groq client
_groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

_todo_service = TodoService()

DEFAULT_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")


def _call_function(name: str, arguments: Dict[str, Any]) -> Any:
    """
    Executes an internal tool/function based on model tool-call request.
    Returns JSON-serializable result objects.
    """

    def _convert_enum(value: Any, enum_cls):
        if value is None:
            return None
        try:
            return enum_cls(value)
        except Exception as exc:
            raise ValueError(f"invalid value for {enum_cls.__name__}: {value}") from exc

    if name == "get_tasks":
        return [t.to_dict() for t in _todo_service.get_tasks()]
        
    if name == "add_task":
        task_kwargs = arguments.copy()
        try:
            if "type" in task_kwargs:
                task_kwargs["type"] = _convert_enum(task_kwargs.get("type"), TaskType)
            if "status" in task_kwargs:
                task_kwargs["status"] = _convert_enum(task_kwargs.get("status"), TaskStatus)
            task = Task(**task_kwargs)
        except Exception as err:
            return {"success": False, "error": str(err)}

        _todo_service.add_task(task)
        return {"success": True}

    if name == "update_task":
        code = arguments.pop("code", None)
        if code is None:
            return {"success": False, "error": "code is required"}
        try:
            if "type" in arguments:
                arguments["type"] = _convert_enum(arguments.get("type"), TaskType)
            if "status" in arguments:
                arguments["status"] = _convert_enum(arguments.get("status"), TaskStatus)
        except ValueError as err:
            return {"success": False, "error": str(err)}

        result = _todo_service.update_task(code, **arguments)
        return {"success": result}

    if name == "delete_task":
        code = arguments.get("code")
        if not code:
            return {"success": False, "error": "code is required"}
        result = _todo_service.delete_task(code)
        return {"success": result}

    raise ValueError(f"Unknown function: {name}")


def _build_tools() -> List[Dict[str, Any]]:
    """
    Groq uses the 'tools' format (OpenAI-style tools).
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "get_tasks",
                "description": "Retrieve all tasks",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "add_task",
                "description": "Create a new task with the provided fields",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string"},
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "type": {"type": "string", "enum": [t.value for t in TaskType]},
                        "start_date": {"type": "string"},
                        "end_date": {"type": "string"},
                        "status": {"type": "string", "enum": [s.value for s in TaskStatus]},
                    },
                    "required": ["code", "title"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "update_task",
                "description": "Update an existing task identified by code",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string"},
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "type": {"type": "string", "enum": [t.value for t in TaskType]},
                        "start_date": {"type": "string"},
                        "end_date": {"type": "string"},
                        "status": {"type": "string", "enum": [s.value for s in TaskStatus]},
                    },
                    "required": ["code"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "delete_task",
                "description": "Remove a task by its code",
                "parameters": {
                    "type": "object",
                    "properties": {"code": {"type": "string"}},
                    "required": ["code"],
                },
            },
        },
    ]


def _safe_json_loads(raw: Optional[str]) -> Dict[str, Any]:
    """
    Best-effort JSON parse for tool arguments.
    With llama-3.1-8b-instant you may occasionally get malformed JSON.
    Keep this strict (raise) or add repair logic if needed.
    """
    if not raw:
        return {}
    return json.loads(raw)


def agent(query: str) -> str:
    """
    1) Ask the model if it wants to call a tool
    2) If tool call requested: execute tool, then ask model to produce final response
    """
    tools = _build_tools()

    # Round 1: model chooses tool (or answers directly)
    response = _groq_client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[{"role": "user", "content": query}],
        tools=tools,
        tool_choice="auto",
        temperature=0.2,
    )

    message = response.choices[0].message

    # If the model requested tool calls
    tool_calls = getattr(message, "tool_calls", None) or []
    if tool_calls:
        # This example executes ONLY the first tool call.
        # You can loop over all tool_calls if you want multi-step tool execution.
        tool_call = tool_calls[0]
        func_name = tool_call.function.name

        try:
            args = _safe_json_loads(tool_call.function.arguments)
        except json.JSONDecodeError as exc:
            # Return a structured error; alternatively implement a "repair JSON" retry.
            result = {"success": False, "error": f"Invalid JSON arguments: {exc}"}
        else:
            result = _call_function(func_name, args)

        # Round 2: feed tool result back to model
        followup = _groq_client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "user", "content": query},
                # assistant tool call message
                {
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": func_name,
                                "arguments": tool_call.function.arguments,
                            },
                        }
                    ],
                },
                # tool result message
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                },
            ],
            temperature=0.2,
        )
        return followup.choices[0].message.content or ""

    # No tool call; return direct answer
    return message.content or ""