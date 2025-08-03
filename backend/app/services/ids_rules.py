def evaluar_riesgos(resultados):
    alertas = []

    for host in resultados:
        ip = host.get("ip")
        puertos = [p["puerto"] for p in host.get("puertos_abiertos", [])]

        if 23 in puertos:
            alertas.append(f"⚠️ {ip}: Puerto 23 (Telnet) abierto – Riesgo ALTO")
        if 21 in puertos:
            alertas.append(f"⚠️ {ip}: Puerto 21 (FTP) abierto – Riesgo MEDIO (sin cifrado)")
        if 3389 in puertos:
            alertas.append(f"⚠️ {ip}: Puerto 3389 (RDP) abierto – Riesgo ALTO")
        if 445 in puertos:
            alertas.append(f"🚨 {ip}: Puerto 445 (SMB) abierto – RIESGO CRÍTICO")

    return alertas