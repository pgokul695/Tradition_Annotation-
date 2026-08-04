from pathlib import Path
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from .db import Base, engine, get_db
from .services.ingest import ingest, DATA
from .routers import images, annotate, export, stats, models
Base.metadata.create_all(engine) # Alembic is supplied for production migrations; this enables zero-config local development.
app=FastAPI(title="Tradition Annotation Pipeline")
app.add_middleware(CORSMiddleware,allow_origins=["http://localhost:5173", "http://localhost:5003", "https://t3.gokulp.online"],allow_methods=["*"],allow_headers=["*"])
app.mount("/dataset",StaticFiles(directory=DATA/"dataset"),name="dataset")
app.include_router(images.router); app.include_router(annotate.router); app.include_router(export.router); app.include_router(stats.router); app.include_router(models.router)
@app.post("/api/ingest")
def ingest_data(db:Session=Depends(get_db)): return ingest(db)
@app.get("/api/health")
def health(): return {"ok":True}
