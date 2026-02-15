from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import get_settings


def _key_func(request):
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"key:{api_key}"
    return get_remote_address(request)


settings = get_settings()
limiter = Limiter(
    key_func=_key_func,
    default_limits=[f"{settings.rate_limit_requests}/minute"],
    enabled=settings.rate_limit_enabled,
)
