import json
from typing import Any, Dict

import openai
import os
from dotenv import load_dotenv

load_dotenv()

from .todo_service import TodoService
from .entities import Task, TaskType, TaskStatus

openai.api_key = os.getenv("OPENAI_API_KEY")

# single service instance for simplicity
_todo_service = TodoService()


def _call_function(name: str, arguments: Dict[str, Any]) -> Any:
    def _convert_enum(value: Any, enum_cls):
        if value is None:
            return None
        try:
            return enum_cls(value)
        except Exception as exc:
            raise ValueError(f"invalid value for {enum_cls.__name__}: {value}") from exc

    if name == "get_tasks":
        tasks = _todo_service.get_tasks()
        return [t.__dict__ for t in tasks]

    if name == "add_task":
        task_kwargs = arguments.copy()
        try:
            if "type" in task_kwargs:
                task_kwargs["type"] = _convert_enum(task_kwargs.get("type"), TaskType)
            if "status" in task_kwargs:
                task_kwargs["status"] = _convert_enum(task_kwargs.get("status"), TaskStatus)
            task = Task(**task_kwargs)
        except Exception as err:
            # propagate a structured error back to the caller
            return {"success": False, "error": str(err)}
        _todo_service.add_task(task)
        return {"success": True}

    if name == "update_task":
        code = arguments.pop("code", None)
        if code is None:
            return {"success": False, "error": "code is required"}
        try:
            # convert any enum fields present
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


def agent(query: str) -> str:
    # prepare the function definitions for the model
    functions = [
        {
            "name": "get_tasks",
            "description": "Retrieve all tasks",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
        {
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
        {
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
        {
            "name": "delete_task",
            "description": "Remove a task by its code",
            "parameters": {
                "type": "object",
                "properties": {"code": {"type": "string"}},
                "required": ["code"],
            },
        },
    ]

    # first round: ask GPT what function to call
    response = openai.ChatCompletion.create(
        model="gpt-4-0613",
        messages=[{"role": "user", "content": query}],
        functions=functions,
        function_call="auto",
    )

    message = response.choices[0].message
    if message.get("function_call"):
        func_name = message["function_call"]["name"]
        args = json.loads(message["function_call"].get("arguments", "{}"))
        result = _call_function(func_name, args)

        # second round: ask GPT to render a human-friendly response
        followup = openai.ChatCompletion.create(
            model="gpt-4-0613",
            messages=[
                {"role": "user", "content": query},
                message,
                {"role": "function", "name": func_name, "content": json.dumps(result)},
            ],
        )
        return followup.choices[0].message.get("content", "")

    # if the model just responded normally, return that text
    return message.get("content", "")
