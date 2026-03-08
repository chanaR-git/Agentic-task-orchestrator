```markdown
# 🤖 TaskBot Agent: LLM-Powered Task Orchestration

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![Groq](https://img.shields.io/badge/Groq-Cloud-orange?style=for-the-badge)
![Llama3](https://img.shields.io/badge/Meta-Llama_3.1-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.9+-blue?style=for-the-badge&logo=python)

**TaskBot Agent** is an enterprise-grade, full-stack task management system that replaces traditional graphical interfaces with a deterministic, LLM-driven conversational agent. 

## 🎯 The Product Vision

Managing daily tasks has never been easier 😊 

Instead of navigating through complex interfaces and clicking through menus just to view, add, update, or delete tasks... **all this goodness is now in one chat!** 🤖

*   Remembered that you have an event next week? 🤗
*   Need to update the submission date for a report? 📊
*   Want to know what awaits you tomorrow? 🫣

Just tell the chat in free text. The intelligent agent will understand your intent and take care of everything that is needed, perfectly and properly! 

---

## 📸 Project Showcase

The React UI acts as a synchronized observer to the backend's state, updating instantly when the agent executes an internal tool.

![Active State](./assets/active-state.png) 
*The backend returns both the LLM text response and the synchronized database state to React in a single payload.*

![Empty State](./assets/empty-state.png)
*Clean, modern UI built with React and Tailwind CSS.*

---

## 🏗️ Backend Architecture & Engineering Best Practices

This project was engineered to demonstrate robust **Agentic System Design**, treating the LLM not just as a text generator, but as a deterministic reasoning engine bound by strict backend constraints.

### 1. Agentic Orchestration Engine (Two-Round Pipeline)
The backend implements a sophisticated multi-turn orchestration loop to ensure reliable tool execution:
*   **Round 1 (Reasoning & Tool Selection):** The LLM receives the prompt and tools. It evaluates if a backend action is needed. If yes, it outputs a strict JSON tool call.
*   **Local Execution (Observation):** The Python backend intercepts the LLM's request, executes the internal function, and captures the result (or error trace).
*   **Round 2 (Synthesis):** The execution result is injected back into the context window, forcing the LLM to generate a natural language response based *only* on the factual outcome of the backend execution.

### 2. Strict I/O & "Untrusted Client" Validation
LLMs are prone to hallucinations and formatting errors. The backend treats the LLM as an untrusted client:
*   **Pydantic & Enums:** All incoming tool arguments are strictly validated against Python Enums (`TaskType`, `TaskStatus`) and Pydantic models.
*   **Graceful Recovery:** If the LLM generates malformed JSON or hallucinates an unsupported function name, the backend catches the `JSONDecodeError` or `ValueError` and feeds the error *back* to the LLM, prompting it to self-correct in the next turn.

### 3. Multi-Tenant Session Isolation & Concurrency
The API is fully stateless, managing user sessions dynamically in memory:
*   **Data Isolation:** The system maps unique `session_id`s to isolated instances of `TodoService` and conversational histories. User A's data and context are completely hidden from User B.
*   **Service Layer Pattern:** The data access layer (`TodoService`) is decoupled from the agent logic, making it trivial to replace the current in-memory dictionary with a persistent database (e.g., PostgreSQL/SQLAlchemy) without altering the agent's code.

### 4. Token Economics & Context Optimization
Sending full conversation histories to LLMs is expensive and degrades performance. This backend implements advanced memory management:
*   **Dynamic State Injection:** Instead of making the LLM "remember" tasks from past messages, the exact, real-time database state is injected directly into the `SystemPrompt` on every request. 
*   **Sliding Window Memory:** The backend strips out expensive, bulky JSON `tool_calls` and `tool_responses` from older turns, retaining only the last 2-3 text interactions. This preserves anaphora resolution (e.g., understanding *"delete the first one"*) while drastically reducing token consumption and preventing `400 Bad Request` context window errors.

---

## 📋 Task Management Capabilities

The core of the application revolves around a strictly typed **Task** entity. 
Each task contains: `Code`, `Title`, `Description`, `Type`, `Start Date`, `End Date`, and `Status`.

### Agent Tool Arsenal
The AI operates autonomously using the following backend bindings:
*   **Retrieval & Filtering:** Fetching tasks dynamically based on user intent.
*   **Creation:** Parsing unstructured text into structured date/time and category formats.
*   **Mutation:** Updating specific fields dynamically without overwriting the entire task entity.
*   **Deletion:** Safely removing entities based on context resolution.

---

## 🛠️ Tech Stack

**Backend (API & Agent Layer):**
*   **FastAPI:** Asynchronous REST API framework.
*   **Python 3:** Core logic and data structures.
*   **Pydantic:** Data validation and serialization.
*   **Groq SDK:** Ultra-low latency inference API integration.
*   **Meta Llama 3.1 8B Instant:** The LLM reasoning model.

**Frontend (Client Layer):**
*   **React.js:** Component-based UI.
*   **Tailwind CSS:** Utility-first styling.
*   **Framer Motion:** Smooth UI animations.

---

## 🚀 Getting Started

### Prerequisites
*   Node.js (v18+)
*   Python (3.9+)
*   A Groq API Key

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/TaskBot-Agent.git
cd TaskBot-Agent
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the `backend` directory:
```env
GROQ_API_KEY=your_api_key_here
GROQ_MODEL=llama-3.1-8b-instant
```

Start the FastAPI server:
```bash
uvicorn src.main:app --reload
```
*The API will be available at `http://localhost:8000`*

### 3. Frontend Setup
Open a new terminal window:
```bash
cd frontend
npm install
npm run dev
```
*The React app will be available at `http://localhost:5173`*
```