import csv
from pathlib import Path
from sqlalchemy.orm import Session
from ..models import Image, Annotation

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data"
def ingest(db: Session):
    csv_path, dataset = DATA / "metadata.csv", DATA / "dataset"
    added = existing = 0; missing = []; rows = []
    with csv_path.open(encoding="utf-8", newline="") as f: rows = list(csv.DictReader(f))
    filenames = {r["filename"] for r in rows}
    for row in rows:
        image_id = row["image_id"]
        if not (DATA / row["local_path"]).is_file(): missing.append({"image_id": image_id, "local_path": row["local_path"]})
        if db.get(Image, image_id): existing += 1; continue
        db.add(Image(**{k: (v or None) for k,v in row.items()})); db.add(Annotation(image_id=image_id, style=row["style"])); added += 1
    unmatched = [str(p.relative_to(DATA)) for p in dataset.rglob("*") if p.is_file() and p.name not in filenames]
    db.commit()
    return {"added": added, "existing": existing, "missing_metadata_rows": missing, "unmatched_files": unmatched}
