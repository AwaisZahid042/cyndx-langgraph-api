from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.middleware.auth import AuthMiddleware
from app.api.middleware.logging import LoggingMiddleware
from app.api.middleware.rate_limiter import limiter
from app.api.middleware.request_id import RequestIDMiddleware
from app.api.routes import health, messages, sessions
from app.config import get_settings
from app.core.exceptions import AppError
from app.core.logging import setup_logging
from app.services.session_manager import SessionManager

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(log_level=settings.log_level, json_format=not settings.debug)
    app.state.session_manager = SessionManager()
    logger.info(f"{settings.app_name} v{settings.app_version} starting up")
    yield
    logger.info("Shutting down")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Production-grade LangGraph conversational AI API with multi-LLM support.",
        lifespan=lifespan,
    )

    # middleware stack (outermost first)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(AuthMiddleware)
    app.add_middleware(RequestIDMiddleware)

    # rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # routes
    app.include_router(health.router)
    app.include_router(sessions.router)
    app.include_router(messages.router)

    # error handlers
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "unknown")
        return JSONResponse(status_code=exc.status_code, content={
            "error": {"code": exc.error_code, "message": exc.message, "details": exc.details, "request_id": request_id}
        })

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "unknown")
        details = {".".join(str(loc) for loc in e["loc"]): e["msg"] for e in exc.errors()}
        return JSONResponse(status_code=422, content={
            "error": {"code": "VALIDATION_ERROR", "message": "Request validation failed.", "details": details, "request_id": request_id}
        })

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "unknown")
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(status_code=500, content={
            "error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred.", "details": {}, "request_id": request_id}
        })

    return app


app = create_app()
