from fastapi import APIRouter, HTTPException
from ..model_config import configured_models, discover_models

router = APIRouter(prefix="/api", tags=["models"])

@router.get("/models")
def list_models():
    return {"models": configured_models()}

@router.post("/models/refresh")
def refresh_models():
    try:
        return {"models": [{"id": item["id"], "label": item["label"], "provider": item["provider"], "vision_capable": True} for item in discover_models(refresh=True)]}
    except Exception as exc:
        raise HTTPException(502, f"Model discovery failed: {exc}") from exc
