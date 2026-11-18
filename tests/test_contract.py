import json
import re

import anthropic
import httpx
from fastapi.testclient import TestClient

from tests.conftest import AGENT_KEY, CV_PATH

REQUIRED_RESPONSE_FIELDS = {
    "id", "object", "created_at", "completed_at", "status", "incomplete_details", "model",
    "previous_response_id", "instructions", "output", "error", "tools", "tool_choice", "truncation",
    "parallel_tool_calls", "text", "top_p", "presence_penalty", "frequency_penalty", "top_logprobs",
    "temperature", "reasoning", "usage", "max_output_tokens", "max_tool_calls", "store", "background",
    "service_tier", "metadata", "safety_identifier", "prompt_cache_key",
}
STREAM_ORDER = [
    "response.created", "response.in_progress", "response.output_item.added", "response.content_part.added",
    "response.output_text.delta", "response.output_text.delta", "response.output_text.done",
    "response.content_part.done", "response.output_item.done", "response.completed",
]


def user_body(text="Hola", **extra):
    return {"input": [{"type": "message", "role": "user", "content": [{"type": "input_text", "text": text}]}], **extra}


def parse_sse(raw: str):
    events = []
    for block in raw.strip().split("\n\n"):
        if block == "data: [DONE]":
            events.append(("[DONE]", None))
            continue
        lines = dict(line.split(": ", 1) for line in block.split("\n"))
        events.append((lines["event"], json.loads(lines["data"])))
    return events


def test_health_needs_no_auth(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_missing_or_wrong_key_is_401_with_error_shape(client):
    for headers in ({}, {"Authorization": "Bearer wrong"}):
        res = client.post("/v1/responses", json=user_body(), headers=headers)
        assert res.status_code == 401
        assert set(res.json()["error"]) == {"message", "type", "param", "code"}


def test_basic_response_has_resource_shape_and_phase(client, auth):
    res = client.post("/v1/responses", json=user_body(), headers=auth)
    data = res.json()
    assert res.status_code == 200
    assert REQUIRED_RESPONSE_FIELDS <= set(data)
    item = data["output"][0]
    assert {"id", "type", "status"} <= set(item)
    assert item["type"] == "message" and item["role"] == "assistant" and item["phase"] == "final_answer"
    assert item["content"][0]["type"] == "output_text"


def test_history_phase_system_and_extra_fields_are_accepted(client, llm, auth):
    body = {
        "model": "other-model", "temperature": 0.1, "tools": [], "instructions": "Tono formal.",
        "input": [
            {"type": "message", "role": "system", "content": "Responde como pirata."},
            {"type": "message", "role": "user", "content": "Hola"},
            {"type": "message", "role": "assistant", "phase": "commentary", "content": [{"type": "output_text", "text": "Pensando"}]},
            {"type": "message", "role": "assistant", "phase": "final_answer", "content": [{"type": "output_text", "text": "Hola, ¿qué quieres saber?"}]},
            {"type": "message", "role": "user", "content": "¿Dónde trabaja?"},
        ],
    }
    assert client.post("/v1/responses", json=body, headers=auth).status_code == 200
    call = llm.calls[0]
    assert [m["role"] for m in call["messages"]] == ["user", "assistant", "user"]
    assert call["system"].index("Reglas, en orden de prioridad") < call["system"].index("Responde como pirata.")
    assert "Tono formal." in call["system"]


def test_image_input_is_rejected(client, auth):
    body = {"input": [{"type": "message", "role": "user", "content": [{"type": "input_image", "image_url": "x"}]}]}
    res = client.post("/v1/responses", json=body, headers=auth)
    assert res.status_code == 400 and res.json()["error"]["type"] == "invalid_request"


def test_invalid_json_and_missing_input_are_400(client, auth):
    assert client.post("/v1/responses", content="no-json", headers=auth).status_code == 400
    assert client.post("/v1/responses", json={}, headers=auth).status_code == 400


def test_unknown_route_is_404_in_spec_format(client):
    res = client.get("/nope")
    assert res.status_code == 404 and res.json()["error"]["type"] == "not_found"


def test_unexpected_error_is_500_and_logged(client, auth, caplog, monkeypatch):
    def fail(*_):
        raise ValueError("detalle interno")

    monkeypatch.setattr("app.main.build_system_prompt", fail)
    caplog.set_level("INFO", logger="cv_agent")
    res = TestClient(client.app, raise_server_exceptions=False).post("/v1/responses", json=user_body(), headers=auth)
    assert res.status_code == 500 and res.json()["error"]["type"] == "server_error"
    assert "detalle interno" not in res.text
    logged = " ".join(r.getMessage() for r in caplog.records if r.name == "cv_agent")
    assert '"status": 500' in logged and '"error_cause": "ValueError"' in logged and "detalle interno" not in logged


def test_provider_rate_limit_maps_to_429(client, llm, auth):
    request = httpx.Request("POST", "https://api.anthropic.com")
    llm.error = anthropic.RateLimitError("limit", response=httpx.Response(429, request=request), body=None)
    res = client.post("/v1/responses", json=user_body(), headers=auth)
    assert res.status_code == 429 and res.json()["error"]["type"] == "too_many_requests"


def test_provider_failure_maps_to_model_error_and_logs_cause(client, llm, auth, caplog):
    caplog.set_level("INFO", logger="cv_agent")
    llm.error = RuntimeError("boom")
    res = client.post("/v1/responses", json=user_body(), headers=auth)
    assert res.status_code == 500 and res.json()["error"]["type"] == "model_error"
    assert "boom" not in res.text
    logged = " ".join(r.getMessage() for r in caplog.records if r.name == "cv_agent")
    assert '"error_cause": "RuntimeError"' in logged and "boom" not in logged


def test_streaming_event_order_and_fields(client, auth):
    res = client.post("/v1/responses", json=user_body(stream=True), headers=auth)
    assert res.headers["content-type"].startswith("text/event-stream")
    events = parse_sse(res.text)
    assert [name for name, _ in events[:-1]] == STREAM_ORDER and events[-1][0] == "[DONE]"
    sequence = [data["sequence_number"] for name, data in events if data]
    assert sequence == sorted(set(sequence))
    assert all(name == data["type"] for name, data in events if data)


def test_streaming_error_is_followed_by_response_failed(client, llm, auth, caplog):
    caplog.set_level("INFO", logger="cv_agent")
    llm.error = RuntimeError("boom")
    events = parse_sse(client.post("/v1/responses", json=user_body(stream=True), headers=auth).text)
    names = [name for name, _ in events]
    assert names[-2:] == ["error", "response.failed"]
    logged = " ".join(r.getMessage() for r in caplog.records if r.name == "cv_agent")
    assert '"error_type": "model_error", "error_cause": "RuntimeError"' in logged


def test_max_tokens_yields_incomplete(client, llm, auth):
    llm.stop_reason = "max_tokens"
    data = client.post("/v1/responses", json=user_body(), headers=auth).json()
    assert data["status"] == "incomplete" and data["incomplete_details"] == {"reason": "max_output_tokens"}


def test_cors_preflight_for_conformance_site(client):
    res = client.options("/v1/responses", headers={
        "Origin": "https://www.openresponses.org", "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization,content-type",
    })
    assert res.headers["access-control-allow-origin"] == "https://www.openresponses.org"


def test_logs_record_mode_tokens_and_never_the_key(client, auth, caplog):
    caplog.set_level("INFO", logger="cv_agent")
    client.post("/v1/responses", json=user_body("texto privado"), headers=auth)
    client.post("/v1/responses", json=user_body(stream=True), headers=auth)
    logged = " ".join(r.getMessage() for r in caplog.records)
    assert '"mode": "sync"' in logged and '"mode": "stream"' in logged and '"latency_ms"' in logged
    assert logged.count('"input_tokens": 5') == 2 and logged.count('"output_tokens": 3') == 2
    assert AGENT_KEY not in logged and "texto privado" not in logged


def test_cv_has_no_contact_data_and_correct_certification():
    cv = CV_PATH.read_text(encoding="utf-8")
    assert not re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}", cv)
    digit_runs = re.findall(r"\+?\d[\d\s().-]{7,}\d", cv)
    assert all(sum(c.isdigit() for c in run) < 10 for run in digit_runs), "the CV must not contain phone numbers"
    assert cv.count("Certified") == 1 and "Azure Fundamentals" in cv
    assert "linkedin.com/in/daniel-gonzalez-r" in cv
