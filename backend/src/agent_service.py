import json
import os
from typing import Any, Dict, List, Optional, Set

from dotenv import load_dotenv
from fastapi import HTTPException
from groq import BadRequestError, Groq

from .entities import Task, TaskStatus, TaskType
from .todo_service import TodoService

load_dotenv()

_groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
_todo_service = TodoService()

DEFAULT_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

sessions: Dict[str, List[Dict[str, Any]]] = {}
todo_services: Dict[str, TodoService] = {}  # מסד נתונים נפרד לכל משתמש!


def get_session_messages(session_id: str) -> List[Dict[str, Any]]:
    """Retrieves or initializes the message history for a specific user"""
    if session_id not in sessions:
        sessions[session_id] = []
    return sessions[session_id]

def get_todo_service(session_id: str) -> TodoService:
    """שולף את מסד הנתונים הפרטי של המשתמש"""
    if session_id not in todo_services:
        todo_services[session_id] = TodoService()
    return todo_services[session_id]
   
def get_dynamic_system_prompt(session_id:str) -> dict:
    """
    Injects the in-memory 'database' (TodoService) directly into the prompt.
    This costs very few tokens but gives the agent 100% accurate memory of tasks.
    """
    user_db = get_todo_service(session_id)
    tasks = user_db.get_tasks()
    
    # Format the tasks compactly to save tokens
    task_lines = []
    for t in tasks:
        task_lines.append(f"- ID: {t.code} | Title: {t.title} | Status: {t.status.value}")
    
    tasks_text = "\n".join(task_lines) if task_lines else "No tasks currently exist."

    prompt = (
        "You are a task assistant for an INTERNAL task system.\n"
        "You do NOT have internet access and must NOT call any web/search tools (e.g., brave_search).\n"
        "You may ONLY call these tools: get_tasks, add_task, update_task, delete_task.\n"
        "When calling tools, you MUST strictly follow the JSON schema, but don't show json to the user.\n"
        f"Allowed TaskType values: {[t.value for t in TaskType]}\n"
        f"Allowed TaskStatus values: {[s.value for s in TaskStatus]}\n"
        "If you are unsure about a field, complete details which makes sense.\n"
        "--- CURRENT SYSTEM STATE (SOURCE OF TRUTH) ---\n"
        f"{tasks_text}\n"
        "----------------------------------------------\n"
        "If the user asks to modify a task, use the exact task_code from the list above."
    )
    
    return {"role": "system", "content": prompt}


def _call_function(name: str, arguments: Dict[str, Any], session_id: str) -> Any:
    """
    Executes an internal tool/function based on model tool-call request.
    Returns JSON-serializable result objects.
    """
    user_db = get_todo_service(session_id) 
    def _convert_enum(value: Any, enum_cls, map_unknown: bool = False):
        if value is None:
            return None
        try:
            return enum_cls(value)
        except Exception:
            if map_unknown:
                unknown = getattr(enum_cls, "UNKNOWN", None)
                if unknown is not None:
                    return unknown
                for member in enum_cls:
                    if getattr(member, "value", None) == "unknown":
                        return member
            raise ValueError(f"invalid value for {enum_cls.__name__}: {value}")

    if name == "get_tasks":
        return [t.to_dict() for t in user_db.get_tasks()]

    if name == "add_task":
        task_kwargs = arguments.copy()
        try:
            if "type" in task_kwargs:
                task_kwargs["type"] = _convert_enum(task_kwargs.get("type"), TaskType, map_unknown=True)
            if "status" in task_kwargs:
                task_kwargs["status"] = _convert_enum(task_kwargs.get("status"), TaskStatus)
            task = Task(**task_kwargs)
        except Exception as err:
            return {"success": False, "error": str(err)}

        user_db.add_task(task)
        return {"success": True}

    if name == "update_task":
        code = arguments.pop("code", None)
        if code is None:
            return {"success": False, "error": "code is required"}
        try:
            if "type" in arguments:
                arguments["type"] = _convert_enum(arguments.get("type"), TaskType, map_unknown=True)
            if "status" in arguments:
                arguments["status"] = _convert_enum(arguments.get("status"), TaskStatus)
        except ValueError as err:
            return {"success": False, "error": str(err)}

        result = user_db.update_task(code, **arguments)
        return {"success": result}

    if name == "delete_task":
        code = arguments.get("code")
        if not code:
            return {"success": False, "error": "code is required"}
        result = user_db.delete_task(code)
        return {"success": result}

    raise ValueError(f"Unknown function: {name}")


def _build_tools() -> List[Dict[str, Any]]:
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
    if not raw:
        return {}
    return json.loads(raw)


def _retry_without_tools(payload_messages: List[Dict[str, Any]]) -> str:
    """Force a normal assistant response without any tool calls."""
    followup = _groq_client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=payload_messages,
        tool_choice="none",
        temperature=0,
    )
    return followup.choices[0].message.content or ""


def _allowed_tool_names(tools: List[Dict[str, Any]]) -> Set[str]:
    return {t["function"]["name"] for t in tools if t.get("type") == "function"}


def choose_tools( recent_context: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> Any:
    """Round 1: ask model (with tools enabled). Returns SDK message object."""
    response = _groq_client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=recent_context,
        tools=tools,
        tool_choice="auto",
        temperature=0,
    )
    return response.choices[0].message


def call_tools(
    messages: List[Dict[str, Any]],
    allowed_tools: Set[str],
    tool_calls: Any,
    session_id,
    *,
    assistant_content: str,
) :
    """Execute tool calls and append assistant/tool messages. Always returns messages list."""
    tool_calls_list = tool_calls or []
    if not tool_calls_list:
        return

    # Guard: refuse unknown tool types/names
    for tc in tool_calls_list:
        if getattr(tc, "type", None) != "function":
            messages.append(
                {
                    "role": "assistant",
                    "content": "Tool calls are not available. Answer without tools.",
                }
            )
            return
        if tc.function.name not in allowed_tools:
            messages.append(
                {
                    "role": "assistant",
                    "content": (
                        f"Unsupported tool request: {tc.function.name}. "
                        "Answer without calling any tools."
                    ),
                }
            )
            return

    tool_messages: List[Dict[str, Any]] = []
    for tc in tool_calls_list:
        func_name = tc.function.name
        raw_args = tc.function.arguments

        try:
            args = _safe_json_loads(raw_args)
        except json.JSONDecodeError as exc:
            result: Any = {"success": False, "error": f"Invalid JSON arguments: {exc}"}
        else:
            try:
                result = _call_function(func_name, args, session_id)             
            except Exception as exc:
                result = {"success": False, "error": f"Internal tool error: {exc}"}

        tool_messages.append(
            {
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result),
            }
        )

    assistant_msg = {
        "role": "assistant",
        "content": assistant_content or "",
        "tool_calls": [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in tool_calls_list
        ],
    }

    messages.append(assistant_msg)
    messages.extend(tool_messages)
    return 

def get_payload_messages(messages: List[Dict[str, Any]],session_id:str) -> List[Dict[str, Any]]:
    """Get the most recent messages to send as payload, including dynamic system prompt."""
    recent_context = [
        msg for msg in messages 
        if msg["role"] in ["user", "assistant"] and not msg.get("tool_calls")
    ][-4:]# Only include recent user/assistant messages without tool calls to save tokens; 
          #the system prompt has the full state. 
    payload_messages = [get_dynamic_system_prompt(session_id)] + recent_context
    return payload_messages

def agent(query: str, session_id: str = "default") -> str:
    
    messages = get_session_messages(session_id)
    
    tools = _build_tools()  
    allowed = _allowed_tool_names(tools)
    
    messages.append({"role": "user", "content": query})
    
    # Round 1
    try:
        first_message = choose_tools(get_payload_messages(messages, session_id), tools)    
    except BadRequestError:
        # Most commonly tool validation failure; fallback to plain answer
        return _retry_without_tools(get_payload_messages(messages,session_id))

    tool_calls = getattr(first_message, "tool_calls", None) or []
    assistant_content = getattr(first_message, "content", "") or ""

    # No tools needed
    if not tool_calls:
        return assistant_content

    # Execute tools
    call_tools(
        messages,
        allowed,
        tool_calls,
        session_id=session_id,
        assistant_content=assistant_content,
    )

    # If we refused tools (unsupported), just answer without tools
    if not any(m.get("role") == "tool" for m in messages):
        return _retry_without_tools(get_payload_messages(messages,session_id))

    # Round 2 (force no tools)
    try:
        followup = _groq_client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=get_payload_messages(messages,session_id),
            tool_choice="none",
            temperature=0,
        )
    except BadRequestError as err:
        raise HTTPException(status_code=400, detail=getattr(err, "response", None) or str(err))

    return followup.choices[0].message.content or ""