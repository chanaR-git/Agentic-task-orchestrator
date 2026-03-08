from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import sys
from src.agent_service import agent, _todo_service


app = FastAPI()

origins = [
    "http://localhost:5173", 
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

class MessageRequest(BaseModel):
    message: str


@app.post("/message")
async def handle_message(req: MessageRequest):
    """Receive a message from the client and forward it to the agent."""
    print(f"DEBUG: Received message: {req.message}")
    result = agent(req.message)
    current_tasks = [t.to_dict() for t in _todo_service.get_tasks()]
    return {"response": result, "tasks": current_tasks}


def main():
    print("Task Manager System is starting...")
    print(f"Running on Python version: {sys.version}")


if __name__ == "__main__":
    main()