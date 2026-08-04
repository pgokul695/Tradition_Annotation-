import logging
from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db, SessionLocal
from ..models import Image, Annotation, AnnotationHistory
from ..schemas import AnnotateRunRequest
from ..services.gemini_annotator import annotate_file
from ..services.ingest import DATA
from ..model_config import api_key_for, format_gemini_error, resolve_model, validate_model
router=APIRouter(prefix="/api/annotate",tags=["annotate"])
logger = logging.getLogger(__name__)
def run_job(image_ids, style, limit, model_id):
    model = resolve_model(model_id)
    logger.info("Starting annotation batch: model_id=%s api_key_env=%s images=%s", model["id"], model["api_key_env"], len(image_ids))
    db=SessionLocal()
    try:
        q=db.query(Image).join(Annotation).filter(Annotation.status=="pending")
        if image_ids: q=q.filter(Image.image_id.in_(image_ids))
        if style: q=q.filter(Image.style==style)
        if limit is not None: q=q.limit(limit)
        for image in q.all():
            a=image.annotation
            logger.info("Annotating image_id=%s model_id=%s", image.image_id, model["id"])
            try:
                output=annotate_file(DATA / image.local_path, image.style or "Indian traditional art", model_id)
                for k,v in output.items(): setattr(a,k,v)
                a.style=image.style; a.status="annotated"; a.source="ai"
                db.add(AnnotationHistory(image_id=image.image_id,field="annotation",old_value="",new_value="Gemini annotation generated",changed_by="gemini-flash-lite")); db.commit()
                logger.info("Annotated image_id=%s model_id=%s", image.image_id, model["id"])
            except Exception as exc:
                # A transport/quota/model failure is not a review decision. Keep the item
                # eligible for a later retry and record the diagnostic separately.
                a.status="pending"
                detail = f"model_id={model['id']}; {format_gemini_error(exc)}"
                db.add(AnnotationHistory(image_id=image.image_id,field="annotation_error",old_value="",new_value=detail,changed_by="gemini-flash-lite")); db.commit()
                logger.warning("Annotation failed for image_id=%s %s", image.image_id, detail)
    finally: db.close()
@router.post("/run")
def start(tasks: BackgroundTasks, payload: AnnotateRunRequest | None = Body(default=None), db:Session=Depends(get_db)):
    if not db.query(Image).first(): raise HTTPException(400,"Ingest the dataset before annotating")
    payload = payload or AnnotateRunRequest()
    try:
        model = resolve_model(payload.model)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if not api_key_for(model):
        raise HTTPException(400, f"Configured key {model['api_key_env']} is not available")
    try:
        validate_model(model)
    except (ValueError, RuntimeError) as exc:
        logger.error("Configured model validation failed: model_id=%s api_key_env=%s error=%s", model["id"], model["api_key_env"], exc)
        raise HTTPException(400, str(exc)) from exc
    query = db.query(Annotation).filter(Annotation.status == "pending")
    if payload.image_ids:
        requested = set(payload.image_ids)
        runnable = {image_id for (image_id,) in query.filter(Annotation.image_id.in_(requested)).with_entities(Annotation.image_id)}
        skipped_missing = [image_id for (image_id,) in db.query(Annotation.image_id).filter(Annotation.image_id.in_(requested), Annotation.status == "missing_file")]
    else:
        runnable = {image_id for (image_id,) in query.with_entities(Annotation.image_id)}
        skipped_missing = []
    if payload.style:
        runnable = {image_id for (image_id,) in db.query(Annotation.image_id).join(Image).filter(Annotation.image_id.in_(runnable), Image.style == payload.style)}
    queued = sorted(runnable)[:payload.limit] if payload.limit is not None else sorted(runnable)
    tasks.add_task(run_job, queued, None, None, model["id"])
    return {"accepted":True,"message":"Annotation job started","queued":len(queued),"model":model["id"],"skipped_missing_file":skipped_missing}
