import time
import logging
import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class AccessLogMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.logger = logging.getLogger("uvicorn")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        response: Response
        try:
            response = await call_next(request)
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            self.logger.info(
                "access: method=%s path=%s status=%s duration_ms=%.2f request_id=%s",
                request.method,
                request.url.path,
                getattr(locals().get("response"), "status_code", "-"),
                duration_ms,
                req_id,
            )

        response.headers["X-Request-ID"] = req_id
        return response

