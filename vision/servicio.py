"""Servicio de visión: webcam + YOLO -> API de HemoVision (Django) y video en vivo."""
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import cv2
import requests
from ultralytics import YOLO

API = os.environ.get("VISION_API", "http://127.0.0.1:8000/api/vision")
TOKEN = os.environ.get("VISION_TOKEN", "")
ESTACION = os.environ.get("VISION_ESTACION", "EST-07")
CAMARA_ID = os.environ.get("VISION_CAMARA_ID", "CAM-07")
INDICE_CAMARA = int(os.environ.get("VISION_INDICE", "0"))
CLASE_YOLO = os.environ.get("VISION_CLASE", "person")
UMBRAL = float(os.environ.get("VISION_UMBRAL", "0.60"))
CADA_N_CUADROS = int(os.environ.get("VISION_CADA_N", "5"))
PUERTO_VIDEO = int(os.environ.get("VISION_PUERTO", "8001"))
SEGUNDOS_LATIDO = 3
SEGUNDOS_ENTRE_EVENTOS = 10
CABECERAS = {"X-Vision-Token": TOKEN}

_candado = threading.Lock()
_ultimo_jpeg = None


def publicar(cuadro):
    global _ultimo_jpeg
    ok, buffer = cv2.imencode(".jpg", cuadro, [cv2.IMWRITE_JPEG_QUALITY, 70])
    if ok:
        with _candado:
            _ultimo_jpeg = buffer.tobytes()


class Manejador(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.split("?")[0] != "/video":
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        try:
            while True:
                with _candado:
                    jpeg = _ultimo_jpeg
                if jpeg:
                    self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\n\r\n")
                    self.wfile.write(jpeg)
                    self.wfile.write(b"\r\n")
                time.sleep(0.1)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass

    def log_message(self, *args):
        pass


def iniciar_servidor_de_video():
    servidor = ThreadingHTTPServer(("127.0.0.1", PUERTO_VIDEO), Manejador)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    print(f"Video en vivo: http://127.0.0.1:{PUERTO_VIDEO}/video")


def enviar(ruta, datos):
    try:
        r = requests.post(f"{API}/{ruta}/", json=datos, headers=CABECERAS, timeout=3)
        return r.status_code, r.json() if r.content else {}
    except requests.RequestException as error:
        print(f"[aviso] no se pudo enviar a {ruta}: {error}")
        return None, {}


def dibujar(cuadro, cajas):
    for x1, y1, x2, y2, nombre, conf in cajas:
        alerta = nombre == CLASE_YOLO and conf >= UMBRAL
        color = (0, 0, 255) if alerta else (200, 160, 0)
        cv2.rectangle(cuadro, (x1, y1), (x2, y2), color, 2)
        cv2.putText(cuadro, f"{nombre} {conf:.2f}", (x1, max(y1 - 6, 14)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    cv2.putText(cuadro, f"{ESTACION} / {CAMARA_ID}", (8, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)


def main():
    if not TOKEN:
        raise SystemExit("Falta la variable VISION_TOKEN (la misma que usa Django).")
    modelo = YOLO("yolov8n.pt")
    nombres = modelo.names
    camara = cv2.VideoCapture(INDICE_CAMARA)
    if not camara.isOpened():
        raise SystemExit("No se pudo abrir la cámara. Pruebe VISION_INDICE=1.")

    iniciar_servidor_de_video()
    print(f"Servicio activo: {ESTACION} / {CAMARA_ID}. Ctrl + C para detener.")
    cuadro_n = 0
    cajas = []
    ultimo_latido = 0.0
    ultimo_evento = 0.0
    ultima_publicacion = 0.0
    try:
        while True:
            ok, cuadro = camara.read()
            if not ok:
                print("[aviso] no se pudo leer un fotograma.")
                time.sleep(1)
                continue
            ahora = time.time()
            if ahora - ultimo_latido >= SEGUNDOS_LATIDO:
                codigo, _ = enviar("senal", {"estacion": ESTACION})
                if codigo not in (None, 200):
                    print(f"[aviso] latido rechazado ({codigo}).")
                ultimo_latido = ahora

            cuadro_n += 1
            if cuadro_n % CADA_N_CUADROS == 0:
                resultado = modelo(cuadro, verbose=False)[0]
                cajas = []
                mejor = 0.0
                for caja in resultado.boxes:
                    nombre = nombres[int(caja.cls)]
                    conf = float(caja.conf)
                    x1, y1, x2, y2 = (int(v) for v in caja.xyxy[0])
                    cajas.append((x1, y1, x2, y2, nombre, conf))
                    if nombre == CLASE_YOLO:
                        mejor = max(mejor, conf)
                if mejor >= UMBRAL and ahora - ultimo_evento >= SEGUNDOS_ENTRE_EVENTOS:
                    codigo, cuerpo = enviar("evento", {
                        "identificador": str(uuid.uuid4()),
                        "estacion": ESTACION,
                        "camara": CAMARA_ID,
                        "clase_evento": "hemorragia",
                        "valor": round(mejor * 100, 2),
                        "hora_evento": datetime.now(timezone.utc).isoformat(),
                    })
                    print(f"Evento enviado: confianza {mejor:.2f} -> {codigo} {cuerpo}")
                    ultimo_evento = ahora

            if ahora - ultima_publicacion >= 0.1:
                vista = cuadro.copy()
                dibujar(vista, cajas)
                publicar(vista)
                ultima_publicacion = ahora
    except KeyboardInterrupt:
        print("Servicio detenido.")
    finally:
        camara.release()


if __name__ == "__main__":
    main()
