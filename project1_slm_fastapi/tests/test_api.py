from fastapi.testclient import TestClient

from project1_slm_fastapi.src.slm_api import main


def test_health():
    client = TestClient(main.app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_process_with_mock_ollama(monkeypatch):
    class DummyClient:
        def generate(self, model, prompt):
            return {"response": "résumé mock", "latency_s": 0.01}

    monkeypatch.setattr(main, "client", DummyClient())
    client = TestClient(main.app)
    response = client.post(
        "/nlp/process",
        json={"text": "Bonjour le monde", "model": "mistral", "task": "summarize"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["result"] == "résumé mock"
    assert payload["source"] == "ollama"
