"""Servicio de visión: webcam + YOLO pose -> API de HemoVision (Django) y video en vivo.

El video se lee en un hilo propio que solo conserva el cuadro más reciente, así el
análisis nunca trabaja con cuadros viejos acumulados (atraso) aunque YOLO tarde más
que la cámara en producir un cuadro.
"""
import base64
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
from sangre import DetectorSangre, resaltar, zonas

API = os.environ.get("VISION_API", "http://127.0.0.1:8000/api/vision")
TOKEN = os.environ.get("VISION_TOKEN", "")
ESTACION = os.environ.get("VISION_ESTACION", "EST-07").strip().upper()
CAMARA_ID = os.environ.get("VISION_CAMARA_ID", "CAM-" + ESTACION.split("-")[-1])
INDICE_CAMARA = int(os.environ.get("VISION_INDICE", "0"))
ANALISIS_HZ = float(os.environ.get("VISION_ANALISIS_HZ", "8"))  # análisis máximos por segundo
TAMANO_ANALISIS = int(os.environ.get("VISION_IMGSZ", "480"))     # 640 original, 320 más rápido
DIAGNOSTICO = os.environ.get("VISION_DIAG", "0") == "1"
PUERTO_VIDEO = int(os.environ.get("VISION_PUERTO", "8001"))
FUENTE = os.environ.get("VISION_FUENTE", "").strip()
DELTA_CAIDA = float(os.environ.get("VISION_DELTA_CAIDA", "0.12"))
SEGUNDOS_CAIDA = float(os.environ.get("VISION_SEG_CAIDA", "0.6"))
DELTA_LATERAL = float(os.environ.get("VISION_DELTA_LATERAL", "0.30"))  # 0 la desactiva
VELOCIDAD = float(os.environ.get("VISION_VELOCIDAD", "3.5"))
SEGUNDOS_MOVIMIENTO = float(os.environ.get("VISION_SEG_MOV", "0.8"))
DETECTAR_ROJO = os.environ.get("VISION_ROJO", "1") == "1"
DELTA_ROJO = float(os.environ.get("VISION_DELTA_ROJO", "0.03"))
SEGUNDOS_LATIDO = 3
SEGUNDOS_ENTRE_EVENTOS = 8
INTERVALO_ANALISIS = 1.0 / max(ANALISIS_HZ, 0.5)
NOMBRES = {MAREO: "POSIBLE MAREO", MOVIMIENTO: "MOVIMIENTO BRUSCO",
           "hemorragia": "POSIBLE HEMORRAGIA (rojo)"}
CABECERAS = {"X-Vision-Token": TOKEN}

_candado = threading.Lock()
_ultimo_jpeg = None
_recalibrar = threading.Event()


class Lector(threading.Thread):
    """Lee la cámara en un hilo propio y guarda solo el cuadro más reciente."""

    def __init__(self, camara):
        super().__init__(daemon=True)
        self.camara = camara
        self._bloqueo = threading.Lock()
        self._cuadro = None
        self._numero = 0
        self._hora = 0.0
        self._activo = True

    def run(self):
        ultimo_aviso = 0.0
        while self._activo:
            ok, cuadro = self.camara.read()
            if not ok:
                ahora = time.time()
                if ahora - ultimo_aviso >= 1.0:
                    print("[aviso] no se pudo leer un fotograma.")
                    ultimo_aviso = ahora
                time.sleep(0.2)
                continue
            with self._bloqueo:
                self._cuadro = cuadro
                self._numero += 1
                self._hora = time.time()

    def ultimo(self):
        with self._bloqueo:
            return self._numero, self._cuadro, self._hora

    def detener(self):
        self._activo = False


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


def enviar_latido():
    """Se ejecuta en un hilo aparte para que un Django lento no frene el análisis."""
    codigo, _ = enviar("senal", {"estacion": ESTACION})
    if codigo not in (None, 200):
        print(f"[aviso] latido rechazado ({codigo}).")


def persona_principal(resultado):
    cajas = resultado.boxes
    if cajas is None or len(cajas) == 0 or resultado.keypoints is None:
        return None
    areas = [
        ((x2 - x1) * (y2 - y1), i)
        for i, (x1, y1, x2, y2) in enumerate(cajas.xyxy.tolist())
    ]
    return max(areas)[1]


def rotular(vista, detector, sangre, recientes, ahora):
    alto = vista.shape[0]
    cv2.putText(vista, f"{ESTACION} / {CAMARA_ID}", (8, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    if not detector.calibrado:
        texto = "Calibrando... quede quieto"
    elif detector.caida is None:
        texto = "Postura no medible (hombros ocultos)"
    else:
        vel = detector.velocidad_actual or 0.0
        lado = (detector.lateral or 0.0) - (detector.base_lateral or 0.0)
        texto = f"caida {detector.caida - detector.base:+.2f} | lado {lado:+.2f} | vel {vel:.1f}"
    cv2.putText(vista, texto, (8, alto - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)
    if DETECTAR_ROJO and sangre.fraccion is not None:
        estado = f"base {sangre.base*100:.1f}%" if sangre.calibrado else "calibrando"
        cv2.putText(vista, f"rojo {sangre.fraccion*100:.1f}% ({estado})", (8, alto - 32),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
    y = 46
    for clase, cuando in recientes.items():
        if ahora - cuando < 5:
            cv2.putText(vista, f"ALERTA: {NOMBRES.get(clase, clase)}", (8, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            y += 26


def captura_jpeg(vista):
    ok, buffer = cv2.imencode(".jpg", vista, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return base64.b64encode(buffer.tobytes()).decode("ascii") if ok else ""


def main():
    if not TOKEN:
        raise SystemExit("Falta la variable VISION_TOKEN (la misma que usa Django).")
    modelo = YOLO("yolov8n-pose.pt")
    camara = (
        cv2.VideoCapture(int(FUENTE) if FUENTE.isdigit() else FUENTE)
        if FUENTE else cv2.VideoCapture(INDICE_CAMARA)
    )
    if not camara.isOpened():
        raise SystemExit("No se pudo abrir la cámara. Pruebe VISION_INDICE=1.")
    try:
        camara.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    except Exception:  # noqa: BLE001 - no todos los controladores lo aceptan
        pass
    detector = Detector(
        delta_caida=DELTA_CAIDA, segundos_caida=SEGUNDOS_CAIDA,
        delta_lateral=DELTA_LATERAL, velocidad=VELOCIDAD,
        segundos_movimiento=SEGUNDOS_MOVIMIENTO,
    )
    sangre = DetectorSangre(delta=DELTA_ROJO)
    rects_sangre = []

    iniciar_servidor_de_video()
    print(f"Servicio activo: {ESTACION} / {CAMARA_ID}. Ctrl + C para detener.")
    print(f"Análisis: hasta {ANALISIS_HZ:g} por segundo a tamaño {TAMANO_ANALISIS}.")
    print("Calibrando 5 segundos: quede quieto y sin el objeto rojo en cuadro.")
    lector = Lector(camara)
    lector.start()
    ultimo_numero = 0
    ultimo = None
    ultimo_latido = 0.0
    ultimo_analisis = 0.0
    ultimo_evento = {}
    recientes = {}
    ultima_publicacion = 0.0
    ultimo_diag = time.time()
    ms_yolo, edades = [], []
    try:
        while True:
            numero, cuadro, hora_cuadro = lector.ultimo()
            if cuadro is None or numero == ultimo_numero:
                time.sleep(0.005)
                continue
            ultimo_numero = numero
            ahora = time.time()
            if _recalibrar.is_set():
                _recalibrar.clear()
                detector.reiniciar_calibracion()
                sangre.reiniciar()
                print("Recalibrando: quede quieto 5 segundos, sin el objeto rojo.")
            if ahora - ultimo_latido >= SEGUNDOS_LATIDO:
                threading.Thread(target=enviar_latido, daemon=True).start()
                ultimo_latido = ahora

            if ahora - ultimo_analisis >= INTERVALO_ANALISIS:
                ultimo_analisis = ahora
                ultimo = modelo(cuadro, imgsz=TAMANO_ANALISIS, verbose=False)[0]
                if DIAGNOSTICO:
                    fin = time.time()
                    ms_yolo.append((fin - ahora) * 1000)
                    edades.append((fin - hora_cuadro) * 1000)
                i = persona_principal(ultimo)
                activos = set()
                if i is None:
                    detector.sin_persona()
                    rects_sangre = []
                    sangre.actualizar(ahora, None)
                else:
                    kp = ultimo.keypoints
                    xy = kp.xy[i].tolist()
                    conf = kp.conf[i].tolist() if kp.conf is not None else [1.0] * len(xy)
                    activos = detector.actualizar(ahora, xy, conf)
                    if DETECTAR_ROJO:
                        rects_sangre = zonas(xy, conf, cuadro.shape)
                        frac = sangre.medir(cuadro, rects_sangre)
                        if sangre.actualizar(ahora, frac):
                            activos.add("hemorragia")
                for clase in activos:
                    recientes[clase] = ahora
                    if ahora - ultimo_evento.get(clase, 0.0) < SEGUNDOS_ENTRE_EVENTOS:
                        continue
                    valor = 0.95 if clase == "hemorragia" else detector.confianza
                    vista_evento = ultimo.plot(img=cuadro.copy())
                    if DETECTAR_ROJO and rects_sangre:
                        resaltar(vista_evento, rects_sangre)
                    rotular(vista_evento, detector, sangre, recientes, ahora)
                    cv2.putText(vista_evento, datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                                (vista_evento.shape[1] - 200, 20),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                    captura = captura_jpeg(vista_evento)
                    codigo, cuerpo = enviar("evento", {
                        "identificador": str(uuid.uuid4()),
                        "estacion": ESTACION,
                        "camara": CAMARA_ID,
                        "clase_evento": clase,
                        "valor": round(valor * 100, 2),
                        "hora_evento": datetime.now(timezone.utc).isoformat(),
                        "captura": captura,
                    })
                    print(f"Evento {clase} -> {codigo} {cuerpo}")
                    ultimo_evento[clase] = ahora

            if ahora - ultima_publicacion >= 0.1:
                vista = ultimo.plot(img=cuadro.copy()) if ultimo is not None else cuadro.copy()
                if DETECTAR_ROJO and rects_sangre:
                    resaltar(vista, rects_sangre)
                    for x1, y1, x2, y2 in rects_sangre:
                        cv2.rectangle(vista, (x1, y1), (x2, y2), (0, 0, 255), 1)
                rotular(vista, detector, sangre, recientes, ahora)
                publicar(vista)
                ultima_publicacion = ahora

            if DIAGNOSTICO and ahora - ultimo_diag >= 5.0 and ms_yolo:
                lapso = ahora - ultimo_diag
                print(f"[diag] {len(ms_yolo) / lapso:.1f} análisis/s | "
                      f"YOLO {sum(ms_yolo) / len(ms_yolo):.0f} ms | "
                      f"edad del cuadro analizado {sum(edades) / len(edades):.0f} ms")
                ms_yolo, edades = [], []
                ultimo_diag = ahora
    except KeyboardInterrupt:
        print("Servicio detenido.")
    finally:
        lector.detener()
        lector.join(timeout=1.0)
        camara.release()


if __name__ == "__main__":
    main()