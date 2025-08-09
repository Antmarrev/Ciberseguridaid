# backend/app/main.py
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from services.scan_service import escanear_red
from services.ids_rules import evaluar_riesgos
from models import ScanResult, SessionLocal, init_db
from sqlalchemy import desc, asc
from datetime import datetime
import io, csv, json

app = FastAPI()
init_db()

# --- helpers ---

def _parse_dt(value: str | None):
    if not value:
        return None
    try:
        # ISO 8601 p.ej. 2025-08-08T00:00:00
        return datetime.fromisoformat(value)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Fecha inválida: {value}. Usa ISO 8601, ej: 2025-08-08T10:30:00")

def _apply_filters(
    db,
    ip: str | None,
    start: str | None,
    end: str | None,
    order_by: str,
    order_dir: str,
    limit: int,
    offset: int,
):
    q = db.query(ScanResult)

    if ip:
        # búsqueda parcial: "192.168.1." o exacta
        q = q.filter(ScanResult.ip.contains(ip))

    dt_start = _parse_dt(start)
    dt_end = _parse_dt(end)

    if dt_start:
        q = q.filter(ScanResult.fecha >= dt_start)
    if dt_end:
        q = q.filter(ScanResult.fecha <= dt_end)

    order_map = {
        "fecha": ScanResult.fecha,
        "ip": ScanResult.ip,
        "id": ScanResult.id,
    }
    col = order_map.get(order_by.lower())
    if not col:
        raise HTTPException(status_code=400, detail=f"order_by inválido: {order_by}. Usa: fecha, ip, id")

    direction = desc if order_dir.lower() == "desc" else asc
    q = q.order_by(direction(col))

    # seguridad en paginación
    limit = max(1, min(limit, 1000))
    offset = max(0, offset)
    return q.offset(offset).limit(limit).all()

# --- endpoints ---

@app.get("/scan")
def escaneo(ip: str = Query(...)):
    resultados = escanear_red(ip)

    # alertas por host (no globales)
    db = SessionLocal()
    try:
        for host in resultados:
            alertas_host = evaluar_riesgos([host])
            db.add(ScanResult(
                ip=host["ip"],
                puertos_abiertos=json.dumps(host["puertos_abiertos"]),
                alertas=json.dumps(alertas_host)
            ))
        db.commit()
    finally:
        db.close()

    # opcional: alertas agregadas (todas juntas) por comodidad de cliente
    alertas_agregadas = []
    for h in resultados:
        alertas_agregadas.extend(evaluar_riesgos([h]))

    return {"resultados": resultados, "alertas": alertas_agregadas}

@app.get("/history")
def history(
    ip: str | None = Query(None, description="Coincidencia parcial o exacta"),
    start: str | None = Query(None, description="ISO 8601: 2025-08-08T00:00:00"),
    end: str | None = Query(None, description="ISO 8601: 2025-08-08T23:59:59"),
    order_by: str = Query("fecha", regex="^(fecha|ip|id)$"),
    order_dir: str = Query("desc", regex="^(asc|desc)$"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    db = SessionLocal()
    try:
        rows = _apply_filters(db, ip, start, end, order_by, order_dir, limit, offset)
        return [
            {
                "id": r.id,
                "ip": r.ip,
                "puertos_abiertos": json.loads(r.puertos_abiertos),
                "alertas": json.loads(r.alertas),
                "fecha": r.fecha.isoformat(),
            } for r in rows
        ]
    finally:
        db.close()

@app.get("/history/export")
def history_export(
    ip: str | None = None,
    start: str | None = None,
    end: str | None = None,
    order_by: str = "fecha",
    order_dir: str = "desc",
    limit: int = 1000,
    offset: int = 0,
    format: str = Query("csv", regex="^(csv|json)$"),
):
    db = SessionLocal()
    try:
        rows = _apply_filters(db, ip, start, end, order_by, order_dir, limit, offset)
        data = [
            {
                "id": r.id,
                "ip": r.ip,
                "fecha": r.fecha.isoformat(),
                "puertos_abiertos": r.puertos_abiertos,  # JSON en texto
                "alertas": r.alertas,                    # JSON en texto
            } for r in rows
        ]
    finally:
        db.close()

    if format == "json":
        return JSONResponse(content=data)

    # CSV
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["id", "ip", "fecha", "puertos_abiertos", "alertas"])
    writer.writeheader()
    writer.writerows(data)
    buf.seek(0)

    filename = "history.csv"
    return StreamingResponse(
        iter([buf.read()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
