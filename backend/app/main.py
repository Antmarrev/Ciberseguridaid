from fastapi import FastAPI, Query
from services.scan_service import escanear_red

app = FastAPI()

@app.get("/scan")
def escaneo(ip: str = Query("192.168.1.0/24")):
    resultados = escanear_red(ip)
    return {"resultados": resultados}