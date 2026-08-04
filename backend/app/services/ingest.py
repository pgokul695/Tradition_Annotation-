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
        file_exists = (DATA / row["local_path"]).is_file()
        if not file_exists: missing.append({"image_id": image_id, "local_path": row["local_path"]})
        image = db.get(Image, image_id)
        if image:
            existing += 1
            annotation = image.annotation
            if annotation:
                # Reconcile this state on every ingest so restored files re-enter the queue.
                if not file_exists:
                    annotation.status = "missing_file"
                elif annotation.status == "missing_file":
                    annotation.status = "pending"
            continue
        db.add(Image(**{k: (v or None) for k,v in row.items()}))
        db.add(Annotation(image_id=image_id, style=row["style"], status="pending" if file_exists else "missing_file"))
        added += 1
    unmatched = [str(p.relative_to(DATA)) for p in dataset.rglob("*") if p.is_file() and p.name not in filenames]
    db.commit()
    return {"added": added, "existing": existing, "missing_metadata_rows": missing, "unmatched_files": unmatched}
