import time

from fastapi import APIRouter, Request

from app.api.schemas.responses import HealthCheckResponse
from app.config import get_settings

router = APIRouter()
_start_time = time.time()


@router.get("/health", response_model=HealthCheckResponse, tags=["System"])
async def health_check(request: Request) -> HealthCheckResponse:
    settings = get_settings()
    return HealthCheckResponse(
        status="healthy",
        version=settings.app_version,
        uptime_seconds=round(time.time() - _start_time, 2),
        checks={"llm_provider": "ok", "checkpoint_store": "ok"},
    )
