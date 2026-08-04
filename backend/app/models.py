from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

class Image(Base):
    __tablename__ = "images"
    image_id: Mapped[str] = mapped_column(String, primary_key=True)
    filename: Mapped[str | None] = mapped_column(String)
    style: Mapped[str | None] = mapped_column(String, index=True)
    substyle: Mapped[str | None] = mapped_column(String); era: Mapped[str | None] = mapped_column(String)
    artist: Mapped[str | None] = mapped_column(String); artist_known: Mapped[str | None] = mapped_column(String)
    title: Mapped[str | None] = mapped_column(Text); year: Mapped[str | None] = mapped_column(String)
    estimated_year: Mapped[str | None] = mapped_column(String); century: Mapped[str | None] = mapped_column(String)
    historical_period: Mapped[str | None] = mapped_column(String); region: Mapped[str | None] = mapped_column(String)
    state: Mapped[str | None] = mapped_column(String); country: Mapped[str | None] = mapped_column(String)
    museum: Mapped[str | None] = mapped_column(String); collection: Mapped[str | None] = mapped_column(String)
    source: Mapped[str | None] = mapped_column(String); source_type: Mapped[str | None] = mapped_column(String)
    source_url: Mapped[str | None] = mapped_column(Text); image_url: Mapped[str | None] = mapped_column(Text)
    license: Mapped[str | None] = mapped_column(String); authenticity: Mapped[str | None] = mapped_column(String)
    resolution: Mapped[str | None] = mapped_column(String); width: Mapped[str | None] = mapped_column(String)
    height: Mapped[str | None] = mapped_column(String); file_size: Mapped[str | None] = mapped_column(String)
    format: Mapped[str | None] = mapped_column(String); sha256: Mapped[str | None] = mapped_column(String)
    phash: Mapped[str | None] = mapped_column(String); ahash: Mapped[str | None] = mapped_column(String)
    dhash: Mapped[str | None] = mapped_column(String); download_date: Mapped[str | None] = mapped_column(String)
    local_path: Mapped[str | None] = mapped_column(Text); notes: Mapped[str | None] = mapped_column(Text)
    annotation: Mapped["Annotation | None"] = relationship(back_populates="image", uselist=False, cascade="all, delete-orphan")

class Annotation(Base):
    __tablename__ = "annotations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    image_id: Mapped[str] = mapped_column(ForeignKey("images.image_id"), unique=True, index=True)
    status: Mapped[str] = mapped_column(String, default="pending", index=True)
    style: Mapped[str | None] = mapped_column(String)
    objects: Mapped[list] = mapped_column(JSON, default=list); animals: Mapped[list] = mapped_column(JSON, default=list)
    people: Mapped[list] = mapped_column(JSON, default=list); colors: Mapped[list] = mapped_column(JSON, default=list)
    patterns: Mapped[list] = mapped_column(JSON, default=list); religious_elements: Mapped[list] = mapped_column(JSON, default=list)
    scene: Mapped[str | None] = mapped_column(Text); caption: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text); confidence: Mapped[float | None] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String, default="ai"); reviewed_by: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    image: Mapped[Image] = relationship(back_populates="annotation")

class AnnotationHistory(Base):
    __tablename__ = "annotation_history"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    image_id: Mapped[str] = mapped_column(ForeignKey("images.image_id"), index=True)
    field: Mapped[str] = mapped_column(String); old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text); changed_by: Mapped[str] = mapped_column(String)
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
