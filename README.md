# 🛡️ CiberseguridAId

CiberseguridAId es un proyecto personal de seguridad ofensiva y defensiva que combina **FastAPI** (backend) y **Streamlit** (frontend) para ofrecer un entorno rápido y visual de escaneo y análisis de redes, con un estilo vintage tipo terminal hacker.

Este repositorio corresponde a la **Fase 1** del desarrollo.

---

## 🚀 Características del MVP (Fase 1)
- **Escaneo de redes y hosts** usando Nmap.
- **Histórico persistente** de resultados en base de datos.
- **Filtros avanzados** por IP, fecha, hora, orden, límite y offset.
- **Exportación** en CSV y JSON.
- **Dashboard** con métricas y ranking de puertos más detectados.
- **Frontend vintage hacker** con Streamlit, adaptado para usabilidad y estética.

---

## 📦 Tecnologías
- **Backend:** Python 3.11, FastAPI, SQLAlchemy, Nmap.
- **Frontend:** Streamlit, Pandas, CSS personalizado.
- **Base de datos:** SQLite (en desarrollo se puede cambiar a PostgreSQL).
- **Otros:** Requests, Uvicorn.

---

## ⚙️ Instalación y ejecución

### 1️⃣ Clonar repositorio
```bash
git clone https://github.com/usuario/CiberseguridAId.git
cd CiberseguridAId
```
### 2️⃣ Backend
```bash
cd backend/app
python -m uvicorn main:app --reload
Por defecto, se levanta en http://127.0.0.1:8000.
```
### 3️⃣ Frontend
En otra terminal:
```bash
cd frontend
streamlit run streamlit_app.py
Por defecto, se abre en http://localhost:8501.
```
---

## 📌 Próximos pasos (Fase 2)
Implementación de un IDS (Intrusion Detection System) basado en Machine Learning.

Detección de anomalías en tráfico y puertos.

Alertas inteligentes y exportación avanzada.

Modo CLI para automatización.

---

## 📸 Capturas
(Añadir aquí screenshots del dashboard, escaneo y filtros)

---

## 📜 Licencia
Uso personal y educativo.