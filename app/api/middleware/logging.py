import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.services.metrics import record_request_latency

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.time()
        response = await call_next(request)
        latency_ms = (time.time() - start) * 1000

        request_id = getattr(request.state, "request_id", "unknown")
        logger.info("Request completed", extra={
            "request_id": request_id,
            "method": request.method,
            "endpoint": request.url.path,
            "status_code": response.status_code,
            "latency_ms": round(latency_ms, 2),
        })

        record_request_latency(request.url.path, request.method, response.status_code, latency_ms)
        return response
