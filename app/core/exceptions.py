from __future__ import annotations


class AppError(Exception):
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred."

    def __init__(self, message: str | None = None, details: dict | None = None):
        self.message = message or self.__class__.message
        self.details = details or {}
        super().__init__(self.message)


class SessionNotFoundError(AppError):
    status_code = 404
    error_code = "SESSION_NOT_FOUND"
    message = "No active session found with the given ID."


class SessionTerminatedError(AppError):
    status_code = 400
    error_code = "SESSION_TERMINATED"
    message = "This session has been terminated."


class InvalidRequestError(AppError):
    status_code = 400
    error_code = "INVALID_REQUEST"
    message = "The request is malformed or invalid."


class ProviderError(AppError):
    status_code = 503
    error_code = "LLM_PROVIDER_ERROR"
    message = "The LLM provider is unavailable or returned an error."


class RateLimitError(AppError):
    status_code = 429
    error_code = "RATE_LIMITED"
    message = "Too many requests. Please try again later."


class AuthenticationError(AppError):
    status_code = 401
    error_code = "UNAUTHORIZED"
    message = "Missing or invalid API key."
