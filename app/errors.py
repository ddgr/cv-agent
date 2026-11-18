import anthropic


class ApiError(Exception):
    def __init__(self, status: int, type_: str, message: str, param: str | None = None, code: str | None = None,
                 cause: str | None = None):
        super().__init__(message)
        self.status = status
        self.type = type_
        self.message = message
        self.param = param
        self.code = code
        # Exception class name for the logs only; never sent to the client.
        self.cause = cause

    def body(self) -> dict:
        return {"error": {"message": self.message, "type": self.type, "param": self.param, "code": self.code}}


def from_provider(exc: Exception) -> ApiError:
    cause = type(exc).__name__
    if isinstance(exc, anthropic.RateLimitError):
        return ApiError(429, "too_many_requests", "El proveedor del modelo limitó las peticiones. Intenta de nuevo en unos segundos.", code="rate_limit_exceeded", cause=cause)
    return ApiError(500, "model_error", "El proveedor del modelo no pudo completar la respuesta.", code="provider_error", cause=cause)
