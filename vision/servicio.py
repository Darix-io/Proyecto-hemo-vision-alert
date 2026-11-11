"""Servicio de visión: webcam + YOLO pose -> API de HemoVision (Django) y video en vivo."""
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import cv2
import requests
from ultralytics import YOLO

from pose import MAREO, MOVIMIENTO, Detector

API = os.environ.get("VISION_API", "http://127.0.0.1:8000/api/vision")
TOKEN = os.environ.get("VISION_TOKEN", "")
ESTACION = os.environ.get("VISION_ESTACION", "EST-07")
CAMARA_ID = os.environ.get("VISION_CAMARA_ID", "CAM-07")
INDICE_CAMARA = int(os.environ.get("VISION_INDICE", "0"))
CADA_N_CUADROS = int(os.environ.get("VISION_CADA_N", "3"))
PUERTO_VIDEO = int(os.environ.get("VISION_PUERTO", "8001"))
DELTA_CAIDA = float(os.environ.get("VISION_DELTA_CAIDA", "0.25"))
VELOCIDAD = float(os.environ.get("VISION_VELOCIDAD", "6.0"))
SIMULAR_HEMORRAGIA = os.environ.get("VISION_SIMULAR_HEMORRAGIA", "0") == "1"
UMBRAL_SIMULACION = float(os.environ.get("VISION_UMBRAL", "0.60"))
SEGUNDOS_LATIDO = 3
SEGUNDOS_ENTRE_EVENTOS = 10
NOMBRES = {MAREO: "POSIBLE MAREO", MOVIMIENTO: "MOVIMIENTO BRUSCO", "hemorragia": "SIMULACION"}
CABECERAS = {"X-Vision-Token": TOKEN}

_candado = threading.Lock()
_ultimo_jpeg = None
_recalibrar = threading.Event()


def publicar(cuadro):
    global _ultimo_jpeg
    ok, buffer = cv2.imencode(".jpg", cuadro, [cv2.IMWRITE_JPEG_QUALITY, 70])
    if ok:
        with _candado:
            _ultimo_jpeg = buffer.tobytes()


class Manejador(BaseHTTPRequestHandler):
    def do_GET(self):
        ruta = self.path.split("?")[0]
        if ruta == "/recalibrar":
            _recalibrar.set()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("Recalibrando: el paciente debe quedarse quieto 5 segundos.".encode())
            return
        if ruta != "/video":
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
    print(f"Recalibrar:    http://127.0.0.1:{PUERTO_VIDEO}/recalibrar")


def enviar(ruta, datos):
    try:
        r = requests.post(f"{API}/{ruta}/", json=datos, headers=CABECERAS, timeout=3)
        return r.status_code, r.json() if r.content else {}
    except requests.RequestException as error:
        print(f"[aviso] no se pudo enviar a {ruta}: {error}")
        return None, {}


def persona_principal(resultado):
    cajas = resultado.boxes
    if cajas is None or len(cajas) == 0 or resultado.keypoints is None:
        return None
    areas = [
        ((x2 - x1) * (y2 - y1), i)
        for i, (x1, y1, x2, y2) in enumerate(cajas.xyxy.tolist())
    ]
    return max(areas)[1]


def rotular(vista, detector, recientes, ahora):
    alto = vista.shape[0]
    cv2.putText(vista, f"{ESTACION} / {CAMARA_ID}", (8, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    if not detector.calibrado:
        texto = "Calibrando... quede quieto"
    elif detector.caida is None:
        texto = "Postura no medible (hombros o cabeza ocultos)"
    else:
        vel = detector.velocidad_actual or 0.0
        texto = f"caida {detector.caida - detector.base:+.2f} | vel {vel:.1f}"
    cv2.putText(vista, texto, (8, alto - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)
    y = 46
    for clase, cuando in recientes.items():
        if ahora - cuando < 5:
            cv2.putText(vista, f"ALERTA: {NOMBRES.get(clase, clase)}", (8, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            y += 26


def main():
    if not TOKEN:
        raise SystemExit("Falta la variable VISION_TOKEN (la misma que usa Django).")
    modelo = YOLO("yolov8n-pose.pt")
    camara = cv2.VideoCapture(INDICE_CAMARA)
    if not camara.isOpened():
        raise SystemExit("No se pudo abrir la cámara. Pruebe VISION_INDICE=1.")
    detector = Detector(delta_caida=DELTA_CAIDA, velocidad=VELOCIDAD)

    iniciar_servidor_de_video()
    print(f"Servicio activo: {ESTACION} / {CAMARA_ID}. Ctrl + C para detener.")
    print("Calibrando 5 segundos: el paciente debe quedarse quieto.")
    cuadro_n = 0
    ultimo = None
    ultimo_latido = 0.0
    ultimo_evento = {}
    recientes = {}
    ultima_publicacion = 0.0
    try:
        while True:
            ok, cuadro = camara.read()
            if not ok:
                print("[aviso] no se pudo leer un fotograma.")
                time.sleep(1)
                continue
            ahora = time.time()
            if _recalibrar.is_set():
                _recalibrar.clear()
                detector.reiniciar_calibracion()
                print("Recalibrando: el paciente debe quedarse quieto 5 segundos.")
            if ahora - ultimo_latido >= SEGUNDOS_LATIDO:
                codigo, _ = enviar("senal", {"estacion": ESTACION})
                if codigo not in (None, 200):
                    print(f"[aviso] latido rechazado ({codigo}).")
                ultimo_latido = ahora

            cuadro_n += 1
            if cuadro_n % CADA_N_CUADROS == 0:
                ultimo = modelo(cuadro, verbose=False)[0]
                i = persona_principal(ultimo)
                activos = set()
                if i is None:
                    detector.sin_persona()
                else:
                    kp = ultimo.keypoints
                    xy = kp.xy[i].tolist()
                    conf = kp.conf[i].tolist() if kp.conf is not None else [1.0] * len(xy)
                    activos = detector.actualizar(ahora, xy, conf)
                    if SIMULAR_HEMORRAGIA and float(ultimo.boxes.conf[i]) >= UMBRAL_SIMULACION:
                        activos.add("hemorragia")
                for clase in activos:
                    recientes[clase] = ahora
                    if ahora - ultimo_evento.get(clase, 0.0) < SEGUNDOS_ENTRE_EVENTOS:
                        continue
                    valor = (
                        float(ultimo.boxes.conf[i]) if clase == "hemorragia"
                        else detector.confianza
                    )
                    codigo, cuerpo = enviar("evento", {
                        "identificador": str(uuid.uuid4()),
                        "estacion": ESTACION,
                        "camara": CAMARA_ID,
                        "clase_evento": clase,
                        "valor": round(valor * 100, 2),
                        "hora_evento": datetime.now(timezone.utc).isoformat(),
                    })
                    print(f"Evento {clase} -> {codigo} {cuerpo}")
                    ultimo_evento[clase] = ahora

            if ahora - ultima_publicacion >= 0.1:
                vista = ultimo.plot(img=cuadro.copy()) if ultimo is not None else cuadro.copy()
                rotular(vista, detector, recientes, ahora)
                publicar(vista)
                ultima_publicacion = ahora
    except KeyboardInterrupt:
        print("Servicio detenido.")
    finally:
        camara.release()


if __name__ == "__main__":
    main()
