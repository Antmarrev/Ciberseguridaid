# frontend/streamlit_app.py
import os
import json
from datetime import datetime, time
from typing import Optional, Dict, Any

import requests
import pandas as pd
import streamlit as st

# ----------------------------
# Config inicial
# ----------------------------
st.set_page_config(page_title="CiberseguridAId", page_icon="🛡️", layout="wide")

# Estilo vintage hacker (CRT/terminal)
st.markdown("""
<style>
/* Fuente y fondo */
@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;600&display=swap');
:root {
  --bg: #0d0d0d;
  --bg-soft: #111111;
  --fg: #00ff66;            /* verde fosforescente */
  --fg-soft: #7cffb1;       /* verde claro */
  --accent-amber: #ffcc00;  /* ámbar */
  --accent-red: #ff3333;    /* rojo alerta */
  --border: #004d26;        /* borde verde oscuro */
}
html, body, .stApp { background-color: var(--bg) !important; color: var(--fg) !important; }
*, h1, h2, h3, h4, h5, h6 { font-family: "Fira Code", monospace !important; }

/* Títulos con glow suave */
h1, h2, h3 { text-shadow: 0 0 6px rgba(0,255,102,0.35); }

/* Contenedores principales */
.block-container { padding-top: 1.2rem; }

/* Inputs y selects */
.stTextInput>div>div>input,
.stNumberInput input,
.stSelectbox > div > div,
.stDateInput input,
.stTimeInput input,
.stTextArea textarea {
  background: var(--bg-soft) !important;
  color: var(--fg) !important;
  border: 1px solid var(--border) !important;
  border-radius: 4px !important;
}

/* Botones */
.stButton>button {
  background: var(--bg-soft) !important;
  color: var(--fg) !important;
  border: 1px solid var(--fg) !important;
  border-radius: 4px !important;
  transition: transform .05s ease-in-out, background .15s;
}
.stButton>button:hover { background: var(--fg) !important; color: var(--bg) !important; transform: translateY(-1px); }
.stDownloadButton>button { border: 1px solid var(--fg) !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { border-bottom: 1px solid var(--border) !important; }
.stTabs [data-baseweb="tab"] {
  color: var(--fg);
  background: transparent;
  border-right: 1px dashed var(--border);
}
.stTabs [aria-selected="true"] { background: #0f2016 !important; }

/* Métricas */
[data-testid="stMetric"] { background: #0f2016; border: 1px solid var(--border); border-radius: 6px; padding: .6rem; }

/* Tablas */
.dataframe, .stDataFrame, .stDataFrame div {
  color: var(--fg) !important;
}
thead tr { background: var(--bg-soft) !important; }
tbody tr { background: var(--bg) !important; }
tbody tr:hover { background: #0f2016 !important; }
.stDataFrame [data-testid="stTable"] { border: 1px solid var(--border); border-radius: 6px; }

/* Badges (alertas) */
.badge {
  padding: 4px 8px; border-radius: 12px; margin-right: 6px; white-space: nowrap;
  border: 1px solid var(--border);
}
.badge-ok     { background:#10381f; color:#6dffac; }
.badge-high   { background:#3a2a00; color:#ffcc00; }  /* Alto (ámbar) */
.badge-crit   { background:#2a0000; color:#ff6b6b; border-color:#5a0000; }  /* Crítico (rojo) */
.badge-med    { background:#1b1f24; color:#cbd5e1; }

/* Línea divisoria tipo terminal */
.hr-term { border: 0; border-top: 1px dashed var(--border); margin: 1rem 0; }

/* Scrollbar */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: var(--bg-soft); }
::-webkit-scrollbar-thumb { background: var(--fg); border-radius: 4px; }

/* Cursor parpadeante */
.blink { animation: blink 1s step-end infinite; }
@keyframes blink { 50% { opacity: 0; } }
</style>
""", unsafe_allow_html=True)

DEFAULT_API = "http://127.0.0.1:8000"
if "API_BASE_URL" not in st.session_state:
    st.session_state.API_BASE_URL = os.getenv("API_BASE_URL", DEFAULT_API)

# ----------------------------
# Helpers
# ----------------------------
def get_api_base() -> str:
    return st.session_state.get("API_BASE_URL", DEFAULT_API).rstrip("/")

def to_iso(d: Optional[datetime], t: Optional[time]) -> Optional[str]:
    if not d:
        return None
    t = t or time(0, 0, 0)
    return datetime.combine(d, t).isoformat(timespec="seconds")

def safe_get(url: str, params: Dict[str, Any] | None = None, timeout: int = 25):
    try:
        r = requests.get(url, params=params or {}, timeout=timeout)
        return r, None
    except requests.RequestException as e:
        return None, str(e)

@st.cache_data(ttl=15, show_spinner=False)
def fetch_history_cached(base: str, params: Dict[str, Any]):
    r, err = safe_get(f"{base}/history", params)
    if err:
        return None, err
    if r.status_code != 200:
        return None, f"{r.status_code} - {r.text}"
    try:
        data = r.json()
    except Exception:
        return None, "Respuesta no es JSON"
    return data, None

def fetch_history(base: str, params: Dict[str, Any]):
    return fetch_history_cached(base, params)

def export_history(base: str, params: Dict[str, Any], fmt: str):
    p = params.copy()
    p["format"] = fmt
    r, err = safe_get(f"{base}/history/export", p, timeout=60)
    return r, err

def run_scan(base: str, ip: str):
    r, err = safe_get(f"{base}/scan", params={"ip": ip}, timeout=90)
    return r, err

def render_alert_badges(alertas: list[str]) -> str:
    if not alertas:
        return '<span class="badge badge-ok">Sin alertas</span>'
    chips = []
    for a in alertas:
        sev = "med"
        txt = a.lower()
        if "crítico" in txt or "riesgo crítico" in txt or "🚨" in a:
            sev = "crit"
        elif "alto" in txt or "⚠️" in a:
            sev = "high"
        elif "medio" in txt:
            sev = "med"
        klass = {
            "crit": "badge badge-crit",
            "high": "badge badge-high",
            "med":  "badge badge-med",
        }[sev]
        chips.append(f'<span class="{klass}">{a}</span>')
    return "".join(chips)

def flatten_history_rows(rows: list[dict]) -> pd.DataFrame:
    records = []
    for r in rows:
        ports = r.get("puertos_abiertos", [])
        ports_str = ", ".join(f'{p.get("puerto")}:{p.get("servicio")}' for p in ports) if isinstance(ports, list) else str(ports)
        alerts = r.get("alertas", [])
        alerts_str = " | ".join(alerts) if isinstance(alerts, list) else str(alerts)
        records.append({
            "id": r.get("id"),
            "ip": r.get("ip"),
            "fecha": r.get("fecha"),
            "puertos": ports_str,
            "alertas": alerts_str,
        })
    df = pd.DataFrame(records)
    if not df.empty:
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
        df = df.sort_values(by="fecha", ascending=False)
    return df

# ----------------------------
# Header (limpio)
# ----------------------------

st.markdown("## CiberseguridAId <span class='blink'>|</span>", unsafe_allow_html=True)

with st.container():
    left, right = st.columns([1.6, 3])
    with left:
        base_input = st.text_input(
            "API base",
            get_api_base(),
            help="URL del backend FastAPI (p. ej. http://127.0.0.1:8000)",
            key="api_base_input",
        )
        if st.button("Guardar API", use_container_width=True):
            st.session_state.API_BASE_URL = base_input.strip()
            st.success(f"API guardada: {get_api_base()}")
            st.cache_data.clear()
    with right:
        st.caption("Modo consola vintage. Ajusta la API o lanza un escaneo desde las pestañas.")

# Orden: Dashboard · Escanear · Histórico · Ajustes
tabs = st.tabs(["📊 Dashboard", "🛰 Escanear", "📚 Histórico", "⚙️ Ajustes"])


# ----------------------------
# TAB: Dashboard
# ----------------------------
with tabs[0]:
    st.subheader("Resumen del sistema")
    params = {"order_by": "fecha", "order_dir": "desc", "limit": 100, "offset": 0}
    data, err = fetch_history(get_api_base(), params)
    if err:
        st.error("No se pudo obtener el histórico.")
        with st.expander("Detalles técnicos"):
            st.code(err)
    else:
        df = flatten_history_rows(data)
        c1, c2, c3 = st.columns(3)
        c1.metric("Registros", len(df))
        if not df.empty:
            last_dt = df["fecha"].max()
            c2.metric("Último escaneo", last_dt.strftime("%Y-%m-%d %H:%M:%S"))
            all_ports = []
            for row in data:
                for p in row.get("puertos_abiertos", []):
                    all_ports.append(str(p.get("puerto")))
            top = pd.Series(all_ports).value_counts().head(5) if all_ports else pd.Series(dtype=int)
            with c3:
                st.write("**Top puertos**")
                if not top.empty:
                    st.dataframe(top.rename_axis("Puerto").reset_index(name="Frecuencia"), use_container_width=True, hide_index=True)
                else:
                    st.info("Aún no hay datos de puertos.")
        st.markdown("<hr class='hr-term' />", unsafe_allow_html=True)
        st.write("**Últimos registros**")
        st.dataframe(df.head(20), use_container_width=True, hide_index=True)

# ----------------------------
# TAB: Escanear
# ----------------------------
with tabs[1]:
    st.subheader("Escanear red / host")
    ip_to_scan = st.text_input("IP o rango (CIDR)", "192.168.1.1", help="Ej.: 192.168.1.1 o 192.168.1.0/24")
    colx = st.columns([1, 1])
    if colx[0].button("🛰 Escanear ahora", type="primary"):
        with st.spinner("Ejecutando escaneo..."):
            r, err = run_scan(get_api_base(), ip_to_scan)
        if err or not r:
            st.error("No se pudo contactar con la API.")
            with st.expander("Detalles técnicos"):
                st.code(str(err))
        elif r.status_code != 200:
            st.error("La API devolvió un error.")
            with st.expander("Detalles técnicos"):
                st.code(f"{r.status_code} - {r.text}")
        else:
            payload = r.json()
            st.success("Escaneo completado.")
            resultados = payload.get("resultados", [])
            alertas_global = payload.get("alertas", [])
            st.write("**Resultados**")
            table = []
            for h in resultados:
                ports = ", ".join(f'{p.get("puerto")}:{p.get("servicio")}' for p in h.get("puertos_abiertos", []))
                table.append({"ip": h.get("ip"), "puertos": ports})
            st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)
            st.write("**Alertas agregadas**")
            st.markdown(render_alert_badges(alertas_global), unsafe_allow_html=True)

# ----------------------------
# TAB: Histórico
# ----------------------------
with tabs[2]:
    st.subheader("Histórico con filtros")
    with st.expander("Filtros", expanded=True):
        f1, f2, f3 = st.columns([1.2, 0.8, 0.8])
        with f1:
            ip_q = st.text_input("IP contiene", "", placeholder="ej. 192.168.1.")
        with f2:
            start_d = st.date_input("Desde (fecha)", value=None, format="YYYY-MM-DD")
            start_t = st.time_input("Desde (hora)", value=time(0, 0))
        with f3:
            end_d = st.date_input("Hasta (fecha)", value=None, format="YYYY-MM-DD")
            end_t = st.time_input("Hasta (hora)", value=time(23, 59))

        o1, o2, o3, o4 = st.columns([0.8, 0.8, 0.8, 0.8])
        with o1:
            order_by = st.selectbox("Ordenar por", ["fecha", "ip", "id"], index=0)
        with o2:
            order_dir = st.radio("Dirección", ["desc", "asc"], horizontal=True, index=0)
        with o3:
            limit = st.number_input("Límite", 1, 1000, 100, step=10)
        with o4:
            offset = st.number_input("Offset", 0, 100000, 0, step=10)

        btns = st.columns([1, 1, 2, 2])
        run_q = btns[0].button("🔎 Buscar", use_container_width=True)
        reset_q = btns[1].button("↺ Limpiar", use_container_width=True)
        export_csv = btns[2].button("⬇️ Export CSV", use_container_width=True)
        export_json = btns[3].button("⬇️ Export JSON", use_container_width=True)

        if reset_q:
            ip_q = ""
            start_d = None; end_d = None
            start_t = time(0, 0); end_t = time(23, 59)
            order_by = "fecha"; order_dir = "desc"
            limit, offset = 100, 0

    query_params = {
        "ip": ip_q or None,
        "start": to_iso(start_d, start_t),
        "end": to_iso(end_d, end_t),
        "order_by": order_by,
        "order_dir": order_dir,
        "limit": int(limit),
        "offset": int(offset),
    }

    if run_q or True:
        data, err = fetch_history(get_api_base(), query_params)
        if err:
            st.error("No se pudo obtener el histórico.")
            with st.expander("Detalles técnicos"):
                st.code(err)
        else:
            df = flatten_history_rows(data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.write("**Alertas por fila**")
            for r in data:
                st.markdown(
                    f"<div style='margin-bottom:6px;'><b>{r.get('ip')}</b> — {render_alert_badges(r.get('alertas', []))}</div>",
                    unsafe_allow_html=True
                )

    if export_csv or export_json:
        fmt = "csv" if export_csv else "json"
        with st.spinner(f"Exportando {fmt.upper()}..."):
            resp, err = export_history(get_api_base(), query_params, fmt)
        if err or not resp or resp.status_code != 200:
            st.error("No se pudo exportar.")
            with st.expander("Detalles técnicos"):
                st.code(err or f"{resp.status_code} - {resp.text if resp else 'Sin respuesta'}")
        else:
            if fmt == "csv":
                st.download_button(
                    "Descargar CSV",
                    data=resp.text,
                    file_name="history.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                content = resp.text
                st.download_button(
                    "Descargar JSON",
                    data=content,
                    file_name="history.json",
                    mime="application/json",
                    use_container_width=True
                )

# ----------------------------
# TAB: Ajustes
# ----------------------------
with tabs[3]:
    st.subheader("Ajustes")
    st.write("Base de la API para este cliente.")
    new_base = st.text_input("API_BASE_URL", get_api_base())
    if st.button("Guardar", key="save_api_base"):
        st.session_state.API_BASE_URL = new_base.strip()
        st.success(f"Guardado: {get_api_base()}")
        st.cache_data.clear()
    st.caption("Consejo: si vas a desplegar, expón FastAPI y apunta este valor a su URL pública.")
