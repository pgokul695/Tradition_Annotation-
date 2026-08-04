import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, cast, String
from sqlalchemy.orm import Session, joinedload
from ..db import get_db
from ..models import Image, Annotation, AnnotationHistory
from ..schemas import AnnotationPatch, BulkIds, BulkStyle, AutoApprove

router = APIRouter(prefix="/api", tags=["images"])
def pack(image, history=False):
    d = {c.name:getattr(image,c.name) for c in Image.__table__.columns}; a=image.annotation
    d["annotation"] = ({c.name:getattr(a,c.name) for c in Annotation.__table__.columns} if a else None)
    if history: d["history"]=[{c.name:getattr(h,c.name) for c in AnnotationHistory.__table__.columns} for h in sorted(image.annotation_history, key=lambda h:h.changed_at, reverse=True)]
    return d
@router.get("/images")
def list_images(status: str|None=None, style: str|None=None, search: str|None=None, tag: str|None=None, reviewer: str|None=None, min_confidence:float|None=None, max_confidence:float|None=None, page:int=1, page_size:int=24, db:Session=Depends(get_db)):
    q=db.query(Image).join(Annotation).options(joinedload(Image.annotation))
    if status: q=q.filter(Annotation.status==status)
    if style: q=q.filter(Annotation.style==style)
    if reviewer: q=q.filter(Annotation.reviewed_by==reviewer)
    if min_confidence is not None: q=q.filter(Annotation.confidence>=min_confidence)
    if max_confidence is not None: q=q.filter(Annotation.confidence<=max_confidence)
    if search:
        like=f"%{search}%"; q=q.filter(or_(Annotation.caption.ilike(like),Annotation.description.ilike(like),cast(Annotation.objects,String).ilike(like)))
    if tag:
        q=q.filter(or_(*[cast(getattr(Annotation,f),String).ilike(f"%{tag}%") for f in ["objects","animals","people"]]))
    total=q.count(); items=q.order_by(Image.image_id).offset((page-1)*page_size).limit(page_size).all()
    return {"items":[pack(i) for i in items],"total":total,"page":page,"page_size":page_size}
@router.get("/images/{image_id}")
def get_image(image_id:str, db:Session=Depends(get_db)):
    image=db.query(Image).options(joinedload(Image.annotation)).filter(Image.image_id==image_id).first()
    if not image: raise HTTPException(404,"Image not found")
    image.annotation_history=db.query(AnnotationHistory).filter_by(image_id=image_id).all()
    return pack(image, True)
@router.patch("/images/{image_id}")
def patch_image(image_id:str, values:AnnotationPatch, db:Session=Depends(get_db)):
    a=db.query(Annotation).filter_by(image_id=image_id).first()
    if not a: raise HTTPException(404,"Annotation not found")
    actor=values.reviewed_by or "reviewer"
    for field,value in values.model_dump(exclude_unset=True, exclude={"reviewed_by"}).items():
        old=getattr(a,field)
        if old != value:
            db.add(AnnotationHistory(image_id=image_id,field=field,old_value=json.dumps(old) if isinstance(old,list) else str(old or ""),new_value=json.dumps(value) if isinstance(value,list) else str(value or ""),changed_by=actor)); setattr(a,field,value)
    a.source="human"; a.reviewed_by=actor; a.status="needs_review" if a.status=="pending" else a.status
    db.commit(); return {"ok":True}
def set_status(ids,status,db):
    rows=db.query(Annotation).filter(Annotation.image_id.in_(ids)).all()
    for a in rows: a.status=status
    db.commit(); return {"updated":len(rows)}
@router.post("/images/{image_id}/approve")
def approve(image_id:str, db:Session=Depends(get_db)): return set_status([image_id],"approved",db)
@router.post("/images/{image_id}/reject")
def reject(image_id:str, db:Session=Depends(get_db)): return set_status([image_id],"rejected",db)
@router.post("/bulk/approve")
def bulk_approve(body:BulkIds, db:Session=Depends(get_db)): return set_status(body.image_ids,"approved",db)
@router.post("/bulk/set-style")
def bulk_style(body:BulkStyle, db:Session=Depends(get_db)):
    for a in db.query(Annotation).filter(Annotation.image_id.in_(body.image_ids)): a.style=body.style; a.source="human"
    db.commit(); return {"updated":len(body.image_ids)}
@router.post("/bulk/auto-approve")
def auto_approve(body:AutoApprove, db:Session=Depends(get_db)):
    approved=db.query(Annotation).filter(Annotation.confidence>=body.confidence_threshold,Annotation.status=="annotated").update({Annotation.status:"approved"},synchronize_session=False)
    flagged=db.query(Annotation).filter(Annotation.confidence<body.needs_review_threshold,Annotation.status=="annotated").update({Annotation.status:"needs_review"},synchronize_session=False)
    db.commit(); return {"approved":approved,"needs_review":flagged}
