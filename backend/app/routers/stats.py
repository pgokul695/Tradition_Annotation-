from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Image, Annotation
router=APIRouter(prefix="/api",tags=["stats"])
@router.get("/stats")
def stats(db:Session=Depends(get_db)):
 total=db.query(Image).count(); counts=dict(db.query(Annotation.status,func.count()).group_by(Annotation.status).all())
 styles=[]
 for style,count,approved in db.query(Annotation.style,func.count(),func.sum(Annotation.status=="approved")).group_by(Annotation.style).all(): styles.append({"style":style,"count":count,"approved":approved or 0,"approval_rate":(approved or 0)/count if count else 0})
 return {"total":total,"pending":counts.get("pending",0),"annotated":counts.get("annotated",0),"approved":counts.get("approved",0),"rejected":counts.get("rejected",0),"needs_review":counts.get("needs_review",0),"missing_file":counts.get("missing_file",0),"styles":styles}
