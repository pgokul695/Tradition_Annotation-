import json
from ..models import Image, Annotation
def json_bytes(rows):
    records=[]
    for image in rows:
        d={c.name:getattr(image,c.name) for c in Image.__table__.columns}; d["annotation"]={c.name:getattr(image.annotation,c.name) for c in Annotation.__table__.columns}; records.append(d)
    return json.dumps(records,ensure_ascii=False,indent=2,default=str).encode()
