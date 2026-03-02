from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def test_handle_message_calls_agent(monkeypatch):
    # monkeypatch the agent function referenced in main to return a predictable result
    from src import main

    def fake_agent(msg):
        assert msg == "hello"
        return "response from agent"

    monkeypatch.setattr(main, "agent", fake_agent)

    response = client.post("/message", json={"message": "hello"})
    assert response.status_code == 200
    assert response.json() == {"response": "response from agent"}
