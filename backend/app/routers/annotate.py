from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db, SessionLocal
from ..models import Image, Annotation, AnnotationHistory
from ..schemas import AnnotationRun
from ..services.gemini_annotator import annotate_file
from ..services.ingest import DATA
router=APIRouter(prefix="/api/annotate",tags=["annotate"])
def run_job(image_ids, style):
    db=SessionLocal()
    try:
        q=db.query(Image).join(Annotation).filter(Annotation.status=="pending")
        if image_ids: q=q.filter(Image.image_id.in_(image_ids))
        if style: q=q.filter(Image.style==style)
        for image in q.all():
            a=image.annotation
            try:
                output=annotate_file(DATA / image.local_path, image.style or "Indian traditional art")
                for k,v in output.items(): setattr(a,k,v)
                a.style=image.style; a.status="annotated"; a.source="ai"
                db.add(AnnotationHistory(image_id=image.image_id,field="annotation",old_value="",new_value="Gemini annotation generated",changed_by="gemini-flash-lite")); db.commit()
            except Exception as exc:
                a.status="needs_review"; db.add(AnnotationHistory(image_id=image.image_id,field="annotation_error",old_value="",new_value=str(exc),changed_by="gemini-flash-lite")); db.commit()
    finally: db.close()
@router.post("/run")
def start(body:AnnotationRun, tasks:BackgroundTasks, db:Session=Depends(get_db)):
    if not db.query(Image).first(): raise HTTPException(400,"Ingest the dataset before annotating")
    tasks.add_task(run_job,body.image_ids,body.style)
    return {"accepted":True,"message":"Annotation job started"}
