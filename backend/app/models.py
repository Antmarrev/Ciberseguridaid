# backend/app/models.py
from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

Base = declarative_base()

class ScanResult(Base):
    __tablename__ = "scan_results"

    id = Column(Integer, primary_key=True, index=True)
    ip = Column(String, index=True)
    puertos_abiertos = Column(String)  # Guardaremos como JSON serializado
    alertas = Column(String)  # Guardaremos como JSON serializado
    fecha = Column(DateTime, default=datetime.utcnow)

# Configuración de la BD
DATABASE_URL = "sqlite:///./scan_results.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
