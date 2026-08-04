"""Live, cached discovery of vision-capable Gemini and Gemma models."""
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import dotenv_values

BACKEND_ROOT = Path(__file__).resolve().parents[1]
SETTINGS_FILE = BACKEND_ROOT / "models.json"
CACHE_FILE = BACKEND_ROOT / ".cache" / "vision_models.json"
# One transparent 1x1 PNG: sufficient to test image-input acceptance.
PROBE_IMAGE = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScL7VwAAAABJRU5ErkJggg=="
DEPRECATED_PREFIXES = ("gemini-2.0-",)

def _settings() -> dict:
    with SETTINGS_FILE.open(encoding="utf-8") as handle:
        return json.load(handle)

def _cache() -> dict:
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"checked_at": 0, "models": []}

def _save_cache(models: list[dict]) -> None:
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps({"checked_at": time.time(), "models": models}, indent=2), encoding="utf-8")

def api_key_for(model: dict[str, str]) -> str | None:
    values = dotenv_values(BACKEND_ROOT / ".env")
    return os.getenv(model["api_key_env"]) or values.get(model["api_key_env"])

def _configured_key_envs() -> list[str]:
    return [name for name in _settings().get("api_key_envs", ["GEMINI_API_KEY"]) if os.getenv(name) or dotenv_values(BACKEND_ROOT / ".env").get(name)]

def _is_candidate(item: dict) -> bool:
    name = item.get("name", "").removeprefix("models/")
    text = f"{name} {item.get('displayName', '')} {item.get('description', '')}".lower()
    if not name.startswith(("gemini-", "gemma-")) or "generateContent" not in item.get("supportedGenerationMethods", []):
        return False
    if name.startswith(DEPRECATED_PREFIXES) or "preview" in text:
        return False
    return not any(term in text for term in ("embedding", "tts", "image", "imagen", "veo", "audio", "live", "robotics", "computer-use"))

def _list_models(key: str) -> list[dict]:
    response = requests.get("https://generativelanguage.googleapis.com/v1beta/models", params={"key": key}, timeout=30)
    response.raise_for_status()
    return response.json().get("models", [])

def _probe_vision(key: str, model_name: str) -> tuple[bool, str | None]:
    payload = {"contents": [{"parts": [
        {"text": "Reply with one word describing whether you received an image."},
        {"inlineData": {"mimeType": "image/png", "data": PROBE_IMAGE}},
    ]}], "generationConfig": {"maxOutputTokens": 4}}
    response = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent", params={"key": key}, json=payload, timeout=45)
    if response.ok:
        return True, None
    try:
        error = response.json().get("error", {})
        return False, f"{error.get('status', 'HTTP_ERROR')} [{response.status_code}]: {error.get('message', response.text)}"
    except ValueError:
        return False, f"HTTP_ERROR [{response.status_code}]: {response.text[:500]}"

def _make_id(name: str, env_name: str) -> str:
    return f"{name}--{env_name.lower()}"

def discover_models(refresh: bool = False) -> list[dict]:
    settings = _settings()
    cached = _cache()
    ttl = int(settings.get("cache_ttl_seconds", 86400))
    if not refresh and cached.get("models") and time.time() - cached.get("checked_at", 0) < ttl:
        return cached["models"]
    discovered: list[dict] = []
    for env_name in _configured_key_envs():
        key = os.getenv(env_name) or dotenv_values(BACKEND_ROOT / ".env").get(env_name)
        try:
            raw_models = _list_models(key)
        except requests.RequestException as exc:
            continue
        for item in filter(_is_candidate, raw_models):
            name = item["name"].removeprefix("models/")
            vision_capable, error = _probe_vision(key, name)
            if not vision_capable:
                continue
            discovered.append({
                "id": _make_id(name, env_name),
                "label": item.get("displayName") or name,
                "provider": "gemma" if name.startswith("gemma-") else "gemini",
                "model_name": name,
                "api_key_env": env_name,
                "vision_capable": True,
                "checked_at": datetime.now(timezone.utc).isoformat(),
            })
    _save_cache(discovered)
    return discovered

def _default(models: list[dict]) -> dict:
    if not models:
        raise ValueError("No confirmed vision-capable Gemini/Gemma models are available. Refresh /api/models after configuring a key.")
    def rank(item: dict) -> tuple:
        # Prefer stable Gemini Flash understanding models, newest semantic version first.
        numbers = tuple(int(part) for part in re.findall(r"\d+", item["model_name"]))
        return (item["provider"] == "gemini", "flash" in item["model_name"], "lite" not in item["model_name"], numbers)
    return max(models, key=rank)

def resolve_model(model_id: str | None = None) -> dict:
    models = discover_models()
    if model_id is None:
        return _default(models)
    for item in models:
        if item["id"] == model_id:
            return item
    raise ValueError(f"INVALID_ARGUMENT: configured/discovered model '{model_id}' is unavailable or has not passed the vision probe")

def configured_models() -> list[dict[str, str]]:
    return [{"id": item["id"], "label": item["label"], "provider": item["provider"], "vision_capable": True} for item in discover_models()]

def validate_model(model: dict) -> None:
    if not model.get("vision_capable"):
        raise ValueError(f"INVALID_ARGUMENT: model '{model.get('model_name')}' is not vision-capable")

def format_gemini_error(exc: Exception) -> str:
    status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    return f"{exc.__class__.__name__}{f' [{status}]' if status else ''}: {str(exc).strip() or repr(exc)}"
