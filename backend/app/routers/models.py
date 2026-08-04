import logging
from fastapi import APIRouter
from ..model_config import configured_models, resolve_model, validate_model

router = APIRouter(prefix="/api", tags=["models"])
logger = logging.getLogger(__name__)

@router.get("/models")
def list_models():
    models = []
    for public_model in configured_models():
        valid, error = True, None
        try:
            validate_model(resolve_model(public_model["id"]))
        except (ValueError, RuntimeError) as exc:
            valid, error = False, str(exc)
            logger.error("Configured model is unavailable: id=%s error=%s", public_model["id"], error)
        models.append({**public_model, "available": valid, "error": error})
    return {"models": models}
