import itertools
import json
import time
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

from .errors import ApiError, from_provider
from .llm import LLM, Completion

TEXT_PART_TYPES = {"input_text", "output_text", "text"}


@dataclass
class ParsedRequest:
    stream: bool
    messages: list[dict]
    client_instructions: list[str] = field(default_factory=list)


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def _content_text(content, param: str) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        raise ApiError(400, "invalid_request", "El contenido del mensaje no es válido.", param=param)
    texts = []
    for part in content:
        if not isinstance(part, dict) or part.get("type") not in TEXT_PART_TYPES:
            raise ApiError(400, "invalid_request", "Solo se admite contenido de texto.", param=param)
        texts.append(part.get("text") or "")
    return "\n".join(texts)


def parse_request(body) -> ParsedRequest:
    if not isinstance(body, dict):
        raise ApiError(400, "invalid_request", "El cuerpo debe ser un objeto JSON.")
    raw_input = body.get("input")
    if isinstance(raw_input, str):
        raw_input = [{"type": "message", "role": "user", "content": raw_input}]
    if not isinstance(raw_input, list) or not raw_input:
        raise ApiError(400, "invalid_request", "El campo input es obligatorio.", param="input")

    client_instructions: list[str] = []
    if isinstance(body.get("instructions"), str):
        client_instructions.append(body["instructions"])

    messages: list[dict] = []
    for index, item in enumerate(raw_input):
        param = f"input[{index}]"
        if not isinstance(item, dict) or item.get("type", "message") != "message":
            raise ApiError(400, "invalid_request", "Solo se admiten items de tipo message.", param=param)
        text = _content_text(item.get("content"), param)
        role = item.get("role")
        if role in ("system", "developer"):
            client_instructions.append(text)
        elif role in ("user", "assistant"):
            if text.strip():
                if messages and messages[-1]["role"] == role:
                    messages[-1]["content"] += f"\n\n{text}"
                else:
                    messages.append({"role": role, "content": text})
        else:
            raise ApiError(400, "invalid_request", "Rol de mensaje no válido.", param=f"{param}.role")

    if not messages or messages[-1]["role"] != "user":
        raise ApiError(400, "invalid_request", "La conversación debe terminar con un mensaje del usuario.", param="input")
    if messages[0]["role"] == "assistant":
        messages.insert(0, {"role": "user", "content": "(inicio de la conversación)"})
    return ParsedRequest(stream=body.get("stream") is True, messages=messages, client_instructions=client_instructions)


def message_item(item_id: str, status: str, text: str | None) -> dict:
    content = [] if text is None else [{"type": "output_text", "text": text, "annotations": []}]
    return {"id": item_id, "type": "message", "status": status, "role": "assistant", "phase": "final_answer", "content": content}


def response_object(resp_id: str, created_at: int, status: str, model: str, max_output_tokens: int,
                    output: list[dict], completion: Completion | None = None, error: dict | None = None) -> dict:
    usage = None
    if completion:
        usage = {
            "input_tokens": completion.input_tokens,
            "output_tokens": completion.output_tokens,
            "total_tokens": completion.input_tokens + completion.output_tokens,
            "input_tokens_details": {"cached_tokens": 0},
            "output_tokens_details": {"reasoning_tokens": 0},
        }
    incomplete = {"reason": "max_output_tokens"} if status == "incomplete" else None
    return {
        "id": resp_id, "object": "response", "created_at": created_at,
        "completed_at": int(time.time()) if status in ("completed", "incomplete") else None,
        "status": status, "incomplete_details": incomplete, "model": model,
        "previous_response_id": None, "instructions": None, "output": output, "error": error,
        "tools": [], "tool_choice": "auto", "truncation": "disabled", "parallel_tool_calls": False,
        "text": {"format": {"type": "text"}}, "top_p": 1.0, "presence_penalty": 0.0, "frequency_penalty": 0.0,
        "top_logprobs": 0, "temperature": 1.0, "reasoning": None, "usage": usage,
        "max_output_tokens": max_output_tokens, "max_tool_calls": None, "store": False, "background": False,
        "service_tier": "default", "metadata": {}, "safety_identifier": None, "prompt_cache_key": None,
    }


def final_status(completion: Completion) -> str:
    return "incomplete" if completion.stop_reason == "max_tokens" else "completed"


async def create_response(llm: LLM, system: str, parsed: ParsedRequest) -> dict:
    created_at = int(time.time())
    try:
        completion = await llm.complete(system, parsed.messages)
    except Exception as exc:
        raise from_provider(exc) from exc
    status = final_status(completion)
    item = message_item(_new_id("msg"), status, completion.text)
    return response_object(_new_id("resp"), created_at, status, llm.model, llm.max_output_tokens, [item], completion)


def _sse(event: dict) -> str:
    return f"event: {event['type']}\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"


async def stream_response(llm: LLM, system: str, parsed: ParsedRequest, outcome: dict) -> AsyncIterator[str]:
    seq = itertools.count()
    resp_id, item_id, created_at = _new_id("resp"), _new_id("msg"), int(time.time())

    def snapshot(status, output, completion=None, error=None):
        return response_object(resp_id, created_at, status, llm.model, llm.max_output_tokens, output, completion, error)

    yield _sse({"type": "response.created", "sequence_number": next(seq), "response": snapshot("in_progress", [])})
    yield _sse({"type": "response.in_progress", "sequence_number": next(seq), "response": snapshot("in_progress", [])})
    yield _sse({"type": "response.output_item.added", "sequence_number": next(seq), "output_index": 0,
                "item": message_item(item_id, "in_progress", None)})
    empty_part = {"type": "output_text", "text": "", "annotations": []}
    yield _sse({"type": "response.content_part.added", "sequence_number": next(seq), "item_id": item_id,
                "output_index": 0, "content_index": 0, "part": empty_part})

    chunks: list[str] = []
    completion: Completion | None = None
    try:
        async for chunk in llm.stream(system, parsed.messages):
            if isinstance(chunk, Completion):
                completion = chunk
                continue
            chunks.append(chunk)
            yield _sse({"type": "response.output_text.delta", "sequence_number": next(seq), "item_id": item_id,
                        "output_index": 0, "content_index": 0, "delta": chunk, "logprobs": []})
    except Exception as exc:
        err = from_provider(exc)
        outcome["error_type"], outcome["error_cause"] = err.type, err.cause
        yield _sse({"type": "error", "sequence_number": next(seq),
                    "error": {"type": err.type, "code": err.code, "message": err.message, "param": None}})
        yield _sse({"type": "response.failed", "sequence_number": next(seq),
                    "response": snapshot("failed", [], error={"code": err.code or err.type, "message": err.message})})
        return

    text = "".join(chunks)
    status = final_status(completion) if completion else "completed"
    if completion:
        outcome["input_tokens"], outcome["output_tokens"] = completion.input_tokens, completion.output_tokens
    part ={"type": "output_text", "text": text, "annotations": []}
    yield _sse({"type": "response.output_text.done", "sequence_number": next(seq), "item_id": item_id,
                "output_index": 0, "content_index": 0, "text": text})
    yield _sse({"type": "response.content_part.done", "sequence_number": next(seq), "item_id": item_id,
                "output_index": 0, "content_index": 0, "part": part})
    item = message_item(item_id, status, text)
    yield _sse({"type": "response.output_item.done", "sequence_number": next(seq), "output_index": 0, "item": item})
    terminal = "response.completed" if status == "completed" else "response.incomplete"
    yield _sse({"type": terminal, "sequence_number": next(seq), "response": snapshot(status, [item], completion)})
    yield "data: [DONE]\n\n"
