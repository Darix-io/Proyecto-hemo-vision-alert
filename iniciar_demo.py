"""Arranque único de HemoVision Alert: Django + cámara del laptop + cámara del celular.

Uso, desde la raíz del proyecto:   python iniciar_demo.py
Un solo Ctrl+C detiene todo. Los registros completos quedan en la carpeta logs/.
"""
import os
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
LOGS = RAIZ / "logs"
TOKEN = "clave-demo-2026"
URL_PANEL = "http://127.0.0.1:8000/"
COLORES = {"DJANGO": "36", "EST-07": "32", "EST-08": "35", "DEMO": "33"}
# Líneas rutinarias de Django que no aportan nada en pantalla (siguen en el log).
RUIDO = re.compile(r'"(GET|HEAD) .* HTTP/1\.1" (200|304)|POST /api/vision/senal/|/static/')

os.system("")  # activa los colores ANSI en la consola de Windows
imprimir_lock = threading.Lock()


def python_de(venv_dir: Path) -> str:
    for ruta in (venv_dir / "Scripts" / "python.exe", venv_dir / "bin" / "python"):
        if ruta.exists():
            return str(ruta)
    raise SystemExit(f"No se encontró el entorno virtual en {venv_dir}")


def decir(etiqueta: str, texto: str) -> None:
    color = COLORES.get(etiqueta, "37")
    with imprimir_lock:
        print(f"\033[{color}m[{etiqueta}]\033[0m {texto}", flush=True)


def leer(proceso, etiqueta, archivo_log):
    with open(archivo_log, "w", encoding="utf-8") as log:
        for linea in proceso.stdout:
            linea = linea.rstrip()
            if not linea:
                continue
            log.write(linea + "\n")
            log.flush()
            if etiqueta == "DJANGO" and RUIDO.search(linea):
                continue
            decir(etiqueta, linea)


def lanzar(etiqueta, comando, carpeta, entorno):
    proceso = subprocess.Popen(
        comando, cwd=carpeta, env=entorno, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
    )
    hilo = threading.Thread(
        target=leer, args=(proceso, etiqueta, LOGS / f"{etiqueta.lower()}.log"), daemon=True)
    hilo.start()
    return proceso


def responde(url: str, espera: float = 2.0) -> bool:
    try:
        urllib.request.urlopen(url, timeout=espera)
        return True
    except urllib.error.HTTPError:
        return True  # el servidor contestó (aunque sea con un error HTTP)
    except Exception:  # noqa: BLE001
        return False


def pedir_ip() -> str:
    if len(sys.argv) > 1:
        return sys.argv[1].strip()
    ip = input("IP del celular (la que muestra IP Webcam, ej. 192.168.0.25). Enter = solo laptop: ").strip()
    return ip


def main() -> int:
    LOGS.mkdir(exist_ok=True)
    ip = pedir_ip()
    if ip.startswith("100."):
        decir("DEMO", "AVISO: una IP que empieza con 100. es de datos móviles; use la del Wi-Fi (192.168...).")
    if ip and not responde(f"http://{ip}:8001/", 4):
        decir("DEMO", f"AVISO: no se alcanza http://{ip}:8001. Revise Wi-Fi, 'Iniciar servidor' y la IP.")
        if input("¿Continuar de todos modos? (s/N): ").strip().lower() != "s":
            return 1

    if responde(URL_PANEL, 1):
        decir("DEMO", "Ya hay algo respondiendo en el puerto 8000. Cierre el Django anterior y vuelva a intentar.")
        return 1

    base = dict(os.environ, PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8", VISION_TOKEN=TOKEN)
    for var in ("VISION_DELTA_CAIDA", "VISION_VELOCIDAD", "VISION_SEG_CAIDA", "VISION_SEG_MOV",
                "VISION_DELTA_LATERAL", "VISION_FUENTE", "VISION_IMGSZ", "VISION_INDICE"):
        base.pop(var, None)
    base.update(VISION_DELTA_ROJO="0.06", VISION_DIAG="0")

    camaras = "EST-07=http://127.0.0.1:8001/video"
    if ip:
        camaras += ",EST-08=http://127.0.0.1:8002/video"

    py_django = python_de(RAIZ / ".venv")
    py_vision = python_de(RAIZ / "vision" / ".venv")
    procesos = []
    try:
        decir("DEMO", "Iniciando Django...")
        procesos.append(("DJANGO", lanzar(
            "DJANGO", [py_django, "manage.py", "runserver", "--noreload"], RAIZ,
            dict(base, VISION_CAMARAS=camaras))))
        for _ in range(60):
            if responde(URL_PANEL):
                break
            if procesos[0][1].poll() is not None:
                decir("DEMO", "Django se detuvo. Revise logs/django.log")
                return 1
            time.sleep(1)
        else:
            decir("DEMO", "Django no respondió en 60 s. Revise logs/django.log")
            return 1
        decir("DEMO", "Django listo.")

        decir("DEMO", "Iniciando cámara del laptop (EST-07)...")
        procesos.append(("EST-07", lanzar(
            "EST-07", [py_vision, "servicio.py"], RAIZ / "vision",
            dict(base, VISION_ESTACION="EST-07", VISION_PUERTO="8001", VISION_IMGSZ="320"))))
        if ip:
            decir("DEMO", f"Iniciando cámara del celular (EST-08) en {ip}...")
            procesos.append(("EST-08", lanzar(
                "EST-08", [py_vision, "servicio.py"], RAIZ / "vision",
                dict(base, VISION_ESTACION="EST-08", VISION_PUERTO="8002",
                     VISION_FUENTE=f"http://{ip}:8001/video"))))

        time.sleep(6)
        webbrowser.open(URL_PANEL)
        decir("DEMO", "Sistema en marcha. Haga un clic en el panel para activar el sonido. Ctrl+C para detener todo.")
        while True:
            time.sleep(1)
            for etiqueta, p in procesos:
                if p.poll() is not None:
                    decir("DEMO", f"AVISO: {etiqueta} se detuvo (código {p.returncode}). Revise logs/{etiqueta.lower()}.log")
                    procesos = [(e, q) for e, q in procesos if q is not p]
                    break
    except KeyboardInterrupt:
        decir("DEMO", "Deteniendo todo...")
    finally:
        for _, p in procesos:
            if p.poll() is None:
                p.terminate()
        for _, p in procesos:
            try:
                p.wait(timeout=6)
            except subprocess.TimeoutExpired:
                p.kill()
        decir("DEMO", "Todo detenido.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
