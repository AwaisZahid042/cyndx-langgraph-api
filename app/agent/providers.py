from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel

# maps model name prefixes to their provider
PROVIDER_PREFIXES = {
    "gpt-": "openai",
    "claude-": "anthropic",
    "gemini-": "google",
    "llama-": "groq",
    "mixtral-": "groq",
    "gemma-": "groq",
}

DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-5-haiku-20241022",
    "google": "gemini-2.0-flash",
    "groq": "llama-3.1-8b-instant",
}


def detect_provider(model: str) -> str:
    for prefix, provider in PROVIDER_PREFIXES.items():
        if model.startswith(prefix):
            return provider
    raise ValueError(f"Unknown model: {model}. Supported prefixes: {list(PROVIDER_PREFIXES.keys())}")


def get_default_model() -> str:
    return DEFAULT_MODELS["openai"]


def get_llm(
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    api_key: str | None = None,
    **kwargs: Any,
) -> BaseChatModel:
    provider = detect_provider(model)

    if provider == "openai":
        from langchain_openai import ChatOpenAI
        params = {"model": model, "temperature": temperature, **kwargs}
        if api_key:
            params["api_key"] = api_key
        return ChatOpenAI(**params)

    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        params = {"model": model, "temperature": temperature, **kwargs}
        if api_key:
            params["anthropic_api_key"] = api_key
        return ChatAnthropic(**params)

    elif provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        params = {"model": model, "temperature": temperature, **kwargs}
        if api_key:
            params["google_api_key"] = api_key
        return ChatGoogleGenerativeAI(**params)

    elif provider == "groq":
        from langchain_groq import ChatGroq
        params = {"model": model, "temperature": temperature, **kwargs}
        if api_key:
            params["groq_api_key"] = api_key
        return ChatGroq(**params)

    else:
        raise ValueError(f"Unsupported provider: {provider}")
