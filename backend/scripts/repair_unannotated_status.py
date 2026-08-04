"""Reset failed, content-empty AI annotations to the pending queue.

Run from backend/: .venv/bin/python scripts/repair_unannotated_status.py
The predicate deliberately excludes human-reviewed rows and any record with
actual annotation content, so legitimate needs_review decisions are preserved.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import or_, update
from app.db import SessionLocal
from app.models import Annotation


def main() -> None:
    statement = (
        update(Annotation)
        .where(
            Annotation.status == "needs_review",
            Annotation.reviewed_by.is_(None),
            or_(Annotation.caption.is_(None), Annotation.caption == ""),
            or_(Annotation.description.is_(None), Annotation.description == ""),
            Annotation.confidence.is_(None),
        )
        .values(status="pending")
    )
    with SessionLocal() as db:
        result = db.execute(statement)
        db.commit()
    print(f"Reset {result.rowcount} empty, unreviewed annotations to pending.")


if __name__ == "__main__":
    main()
