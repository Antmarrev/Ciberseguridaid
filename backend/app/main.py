from fastapi import FastAPI, Query
from services.scan_service import escanear_red
from services.ids_rules import evaluar_riesgos

app = FastAPI()

@app.get("/scan")
def escaneo(ip: str = Query(...)):
    resultados = escanear_red(ip)
    alertas = evaluar_riesgos(resultados)
    return {
        "resultados": resultados,
        "alertas": alertas
    }