import hmac
import json
import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import Settings, load_settings
from .errors import ApiError
from .llm import LLM
from .prompt import build_system_prompt
from .responses import create_response, parse_request, stream_response

logger = logging.getLogger("cv_agent")
CORS_ORIGINS = ["https://www.openresponses.org"]


def _log(request_id: str, mode: str, status: int, started: float, error_type: str | None, model: str,
         usage: dict | None = None, cause: str | None = None) -> None:
    usage = usage or {}
    logger.info(json.dumps({
        "event": "request", "request_id": request_id, "mode": mode, "status": status,
        "latency_ms": round((time.monotonic() - started) * 1000), "error_type": error_type, "error_cause": cause,
        "model": model, "input_tokens": usage.get("input_tokens"), "output_tokens": usage.get("output_tokens"),
    }))


def _error_response(err: ApiError) -> JSONResponse:
    return JSONResponse(err.body(), status_code=err.status)


def create_app(settings: Settings | None = None, llm: LLM | None = None) -> FastAPI:
    settings = settings or load_settings()
    llm = llm or LLM(settings)
    cv_text = settings.cv_path.read_text(encoding="utf-8")
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(
        CORSMiddleware, allow_origins=CORS_ORIGINS, allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.exception_handler(ApiError)
    async def handle_api_error(_: Request, exc: ApiError):
        return _error_response(exc)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(_: Request, exc: StarletteHTTPException):
        kind = "not_found" if exc.status_code == 404 else "invalid_request"
        return _error_response(ApiError(exc.status_code, kind, "Recurso no encontrado." if exc.status_code == 404 else "Petición no válida."))

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, __: RequestValidationError):
        return _error_response(ApiError(400, "invalid_request", "Petición no válida."))

    @app.exception_handler(Exception)
    async def handle_unexpected(_: Request, __: Exception):
        return _error_response(ApiError(500, "server_error", "Error interno del servicio."))

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.post("/v1/responses")
    async def post_responses(request: Request):
        started, request_id = time.monotonic(), uuid.uuid4().hex[:12]
        mode = "unknown"
        try:
            token = request.headers.get("authorization", "").partition(" ")
            if token[0].lower() != "bearer" or not hmac.compare_digest(token[2].encode(), settings.agent_api_key.encode()):
                raise ApiError(401, "invalid_request", "API key inválida o ausente.", code="invalid_api_key")
            try:
                body = await request.json()
            except ValueError:
                raise ApiError(400, "invalid_request", "El cuerpo no es JSON válido.")
            parsed = parse_request(body)
            mode = "stream" if parsed.stream else "sync"
            system = build_system_prompt(cv_text, parsed.client_instructions)

            if not parsed.stream:
                payload = await create_response(llm, system, parsed)
                _log(request_id, mode, 200, started, None, llm.model, payload["usage"])
                return JSONResponse(payload)

            outcome: dict = {}

            async def events():
                try:
                    async for event in stream_response(llm, system, parsed, outcome):
                        yield event
                finally:
                    _log(request_id, mode, 200, started, outcome.get("error_type"), llm.model, outcome,
                         outcome.get("error_cause"))

            return StreamingResponse(events(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})
        except ApiError as err:
            _log(request_id, mode, err.status, started, err.type, llm.model, cause=err.cause)
            raise
        except Exception as exc:
            _log(request_id, mode, 500, started, "server_error", llm.model, cause=type(exc).__name__)
            raise

    return app
