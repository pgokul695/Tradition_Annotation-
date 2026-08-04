from pydantic import BaseModel, Field
from typing import Any

ANNOTATION_FIELDS = ["style","objects","animals","people","colors","patterns","religious_elements","scene","caption","description","confidence"]
class AnnotationPatch(BaseModel):
    style: str | None = None; objects: list[str] | None = None; animals: list[str] | None = None
    people: list[str] | None = None; colors: list[str] | None = None; patterns: list[str] | None = None
    religious_elements: list[str] | None = None; scene: str | None = None; caption: str | None = None
    description: str | None = None; reviewed_by: str | None = None
class AnnotationRun(BaseModel):
    image_ids: list[str] | None = None
    style: str | None = None
class BulkIds(BaseModel): image_ids: list[str]
class BulkStyle(BulkIds): style: str
class AutoApprove(BaseModel): confidence_threshold: float = Field(0.95, ge=0, le=1); needs_review_threshold: float = Field(0.70, ge=0, le=1)
