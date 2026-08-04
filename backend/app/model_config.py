"""Configured, key-safe model registry for annotation runs."""
import json
import os
import time
from pathlib import Path
from dotenv import dotenv_values

BACKEND_ROOT = Path(__file__).resolve().parents[1]
MODELS_FILE = BACKEND_ROOT / "models.json"
_live_models_cache: dict[str, tuple[float, set[str]]] = {}

def _registry() -> dict:
    with MODELS_FILE.open(encoding="utf-8") as handle:
        return json.load(handle)

def configured_models() -> list[dict[str, str]]:
    """Public model metadata only; API keys are never included."""
    return [{"id": item["id"], "label": item["label"]} for item in _registry()["models"]]

def resolve_model(model_id: str | None = None) -> dict[str, str]:
    registry = _registry()
    wanted = model_id or registry["default_model"]
    for item in registry["models"]:
        if item["id"] == wanted:
            return item
    raise ValueError(f"Unknown annotation model: {wanted}")

def api_key_for(model: dict[str, str]) -> str | None:
    # dotenv_values supports dynamically named keys without exposing them via API.
    env_values = dotenv_values(BACKEND_ROOT / ".env")
    return os.getenv(model["api_key_env"]) or env_values.get(model["api_key_env"])

def live_model_names(model: dict[str, str]) -> set[str]:
    """List resource IDs actually available to this key, cached for five minutes."""
    cache_key = model["api_key_env"]
    cached = _live_models_cache.get(cache_key)
    if cached and time.monotonic() - cached[0] < 300:
        return cached[1]
    api_key = api_key_for(model)
    if not api_key:
        raise RuntimeError(f"{model['api_key_env']} is not configured")
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        names = {item.name.removeprefix("models/") for item in client.models.list()}
    except Exception as exc:
        raise RuntimeError(f"Could not list Gemini models for {model['api_key_env']}: {format_gemini_error(exc)}") from exc
    _live_models_cache[cache_key] = (time.monotonic(), names)
    return names

def validate_model(model: dict[str, str]) -> None:
    if model["model_name"] not in live_model_names(model):
        raise ValueError(f"INVALID_ARGUMENT: configured model_name '{model['model_name']}' is not available to {model['api_key_env']}")

def format_gemini_error(exc: Exception) -> str:
    """Preserve provider status/type so 404, quota, and transport failures differ."""
    status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    error_type = exc.__class__.__name__
    message = str(exc).strip() or repr(exc)
    return f"{error_type}{f' [{status}]' if status else ''}: {message}"
