from fastapi import FastAPI
from pydantic import BaseModel

import sys
from .agent_service import agent

app = FastAPI()


class MessageRequest(BaseModel):
    message: str


@app.post("/message")
async def handle_message(req: MessageRequest):
    #"""Receive a message from the client and forward it to the agent."""
    result = agent(req.message)
    return {"response": result}


# keep existing CLI entrypoint for compatibility

def main():
    print("Task Manager System is starting...")
    print(f"Running on Python version: {sys.version}")


if __name__ == "__main__":
    main()