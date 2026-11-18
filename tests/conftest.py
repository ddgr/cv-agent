from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.llm import Completion
from app.main import create_app

AGENT_KEY = "test-agent-key"
CV_PATH = Path(__file__).resolve().parent.parent / "knowledge" / "cv.md"


class FakeLLM:
    model = "fake-model"
    max_output_tokens = 64

    def __init__(self):
        self.calls: list[dict] = []
        self.error: Exception | None = None
        self.stop_reason = "end_turn"

    async def complete(self, system, messages):
        self.calls.append({"system": system, "messages": messages})
        if self.error:
            raise self.error
        return Completion("Respuesta de prueba.", self.stop_reason, 5, 3)

    async def stream(self, system, messages):
        self.calls.append({"system": system, "messages": messages})
        yield "Respuesta "
        if self.error:
            raise self.error
        yield "de prueba."
        yield Completion("Respuesta de prueba.", self.stop_reason, 5, 3)


@pytest.fixture
def llm():
    return FakeLLM()


@pytest.fixture
def client(llm):
    settings = Settings("unused", AGENT_KEY, "fake-model", CV_PATH, 64, 5.0)
    return TestClient(create_app(settings, llm))


@pytest.fixture
def auth():
    return {"Authorization": f"Bearer {AGENT_KEY}"}
