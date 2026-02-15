from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import get_settings

PUBLIC_PATHS = {"/health", "/docs", "/redoc", "/openapi.json", "/"}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        settings = get_settings()

        if not settings.api_key_enabled:
            return await call_next(request)

        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        api_key = request.headers.get("X-API-Key")
        if not api_key or api_key not in settings.api_keys_list:
            request_id = getattr(request.state, "request_id", "unknown")
            return JSONResponse(
                status_code=401,
                content={"error": {"code": "UNAUTHORIZED", "message": "Missing or invalid API key.", "details": {}, "request_id": request_id}},
            )

        return await call_next(request)
