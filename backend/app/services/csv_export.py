import csv, io
from ..models import Image, Annotation
def csv_bytes(rows):
    fields=[c.name for c in Image.__table__.columns]+["caption","description","objects","animals","people","colors","patterns","religious_elements","scene","confidence","status","reviewed_by"]
    out=io.StringIO(); writer=csv.DictWriter(out,fieldnames=fields); writer.writeheader()
    for image in rows:
        row={c.name:getattr(image,c.name) for c in Image.__table__.columns}; a=image.annotation
        row.update({f:getattr(a,f) for f in fields if hasattr(a,f)})
        for f in ["objects","animals","people","colors","patterns","religious_elements"]: row[f]=";".join(row[f] or [])
        writer.writerow(row)
    return out.getvalue().encode()
