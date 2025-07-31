import nmap

def escanear_red(ip_objetivo):
    try:
        nm = nmap.PortScanner()
        resultado = nm.scan(hosts=ip_objetivo, arguments='-T4 -F')
        hosts_resultado = []

        for host in nm.all_hosts():
            puertos_abiertos = []
            if 'tcp' in nm[host]:
                for port, port_data in nm[host]['tcp'].items():
                    if port_data['state'] == 'open':
                        puertos_abiertos.append({
                            "puerto": port,
                            "servicio": port_data.get("name", "desconocido")
                        })
            hosts_resultado.append({
                "ip": host,
                "puertos_abiertos": puertos_abiertos
            })

        return hosts_resultado

    except Exception as e:
        print(f"❌ ERROR en escanear_red: {e}")
        return {"error": str(e)}
