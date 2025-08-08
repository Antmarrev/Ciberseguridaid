from fastapi import FastAPI, Query
from services.scan_service import escanear_red
from services.ids_rules import evaluar_riesgos
from models import ScanResult, SessionLocal, init_db
from sqlalchemy import desc
import json

app = FastAPI()

# Inicializar la BD al arrancar
init_db()

@app.get("/scan")
def escaneo(ip: str = Query(...)):
    resultados = escanear_red(ip)
    alertas = evaluar_riesgos(resultados)

    # Guardar en SQLite
    db = SessionLocal()
    for host in resultados:
        # Calcular alertas solo para este host
        alertas_host = evaluar_riesgos([host])
    
        nuevo_registro = ScanResult(
            ip=host["ip"],
            puertos_abiertos=json.dumps(host["puertos_abiertos"]),
            alertas=json.dumps(alertas_host)
        )
        db.add(nuevo_registro)
    db.commit()
    db.close()

    return {
        "resultados": resultados,
        "alertas": alertas
    }

@app.get("/history")
def historial():
    db = SessionLocal()
    registros = db.query(ScanResult).order_by(desc(ScanResult.fecha)).all()
    db.close()

    return [
        {
            "id": r.id,
            "ip": r.ip,
            "puertos_abiertos": json.loads(r.puertos_abiertos),
            "alertas": json.loads(r.alertas),
            "fecha": r.fecha.isoformat()
        }
        for r in registros
    ]
