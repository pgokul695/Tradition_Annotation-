from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, cast, String
from ..db import get_db
from ..models import Image, Annotation
from ..services.csv_export import csv_bytes
from ..services.json_export import json_bytes
router=APIRouter(prefix="/api/export",tags=["export"])
def rows(db,status,style,search,tag,reviewer,min_confidence,max_confidence):
 q=db.query(Image).join(Annotation).options(joinedload(Image.annotation))
 if status:q=q.filter(Annotation.status==status)
 if style:q=q.filter(Annotation.style==style)
 if reviewer:q=q.filter(Annotation.reviewed_by==reviewer)
 if min_confidence is not None:q=q.filter(Annotation.confidence>=min_confidence)
 if max_confidence is not None:q=q.filter(Annotation.confidence<=max_confidence)
 if search:
  like=f"%{search}%"; q=q.filter(or_(Annotation.caption.ilike(like),Annotation.description.ilike(like),cast(Annotation.objects,String).ilike(like)))
 if tag:q=q.filter(or_(*[cast(getattr(Annotation,f),String).ilike(f"%{tag}%") for f in ["objects","animals","people"]]))
 return q.order_by(Image.image_id).all()
@router.get("/csv")
def export_csv(status:str|None=None,style:str|None=None,search:str|None=None,tag:str|None=None,reviewer:str|None=None,min_confidence:float|None=None,max_confidence:float|None=None,db:Session=Depends(get_db)):
 return Response(csv_bytes(rows(db,status,style,search,tag,reviewer,min_confidence,max_confidence)),media_type="text/csv",headers={"Content-Disposition":"attachment; filename=tradition_annotations.csv"})
@router.get("/json")
def export_json(status:str|None=None,style:str|None=None,search:str|None=None,tag:str|None=None,reviewer:str|None=None,min_confidence:float|None=None,max_confidence:float|None=None,db:Session=Depends(get_db)):
 return Response(json_bytes(rows(db,status,style,search,tag,reviewer,min_confidence,max_confidence)),media_type="application/json",headers={"Content-Disposition":"attachment; filename=tradition_annotations.json"})
