"""Medición de rendimiento del servicio de visión. NO cambia el sistema, solo mide.

Uso (con el servicio detenido y el venv de vision activo):
    python medir.py                      # cámara de la laptop (VISION_INDICE, 0 por defecto)
    VISION_FUENTE=http://IP:8001/video python medir.py   # celular
Pega el resultado completo en el chat.
"""
import os
import statistics
import time

import cv2
import numpy as np

from sangre import mascara_roja

FUENTE = os.environ.get("VISION_FUENTE", "").strip()
INDICE = int(os.environ.get("VISION_INDICE", "0"))
MODELO = os.environ.get("VISION_MODELO", "yolov8n-pose.pt")
CUADROS = int(os.environ.get("MEDIR_CUADROS", "60"))


def abrir():
    return cv2.VideoCapture(FUENTE if FUENTE else INDICE)


def ms(valores):
    return statistics.mean(valores) * 1000, max(valores) * 1000


def captura():
    print("\n== 1. CAPTURA DEL VIDEO ==")
    cam = abrir()
    if not cam.isOpened():
        print("No se pudo abrir la cámara. Cierra otras apps o revisa la dirección.")
        return None
    cuadro = None
    intervalos = []
    anterior = time.time()
    for _ in range(CUADROS):
        ok, c = cam.read()
        if not ok:
            continue
        cuadro = c
        ahora = time.time()
        intervalos.append(ahora - anterior)
        anterior = ahora
    if not intervalos or cuadro is None:
        print("No llegaron cuadros.")
        cam.release()
        return None
    media, peor = ms(intervalos[1:] or intervalos)
    print(f"Resolución: {cuadro.shape[1]}x{cuadro.shape[0]}")
    print(f"Tiempo entre cuadros: media {media:.0f} ms, peor {peor:.0f} ms "
          f"(unos {1000 / media:.1f} cuadros por segundo)")

    print("\n== 2. ATRASO POR COLA DE CUADROS ==")
    print("Se detiene la lectura 1 segundo y luego se leen 10 cuadros seguidos.")
    time.sleep(1.0)
    tiempos = []
    for _ in range(10):
        t = time.time()
        cam.read()
        tiempos.append(time.time() - t)
    rapidos = sum(1 for x in tiempos if x < 0.005)
    print(f"Lecturas instantáneas: {rapidos} de {len(tiempos)}")
    if rapidos >= 4:
        print("-> HAY COLA: OpenCV entrega cuadros viejos. El video y los eventos llegan atrasados.")
    else:
        print("-> No se ve cola de cuadros acumulados.")
    cam.release()
    return cuadro


def rojo(cuadro):
    print("\n== 3. FILTRO DE ROJO ==")
    tiempos = []
    for _ in range(50):
        t = time.time()
        mascara_roja(cuadro)
        tiempos.append(time.time() - t)
    media, peor = ms(tiempos)
    print(f"Filtro sobre el cuadro completo: media {media:.1f} ms, peor {peor:.1f} ms")


def yolo(cuadro):
    print("\n== 4. YOLO (puntos del cuerpo) ==")
    try:
        from ultralytics import YOLO
        modelo = YOLO(MODELO)
    except Exception as e:  # noqa: BLE001
        print(f"No se pudo cargar el modelo ({e}). Ejecuta desde la carpeta vision/.")
        return
    modelo(cuadro, verbose=False)  # calentamiento
    for tam in (640, 480, 320):
        tiempos = []
        for _ in range(15):
            t = time.time()
            modelo(cuadro, imgsz=tam, verbose=False)
            tiempos.append(time.time() - t)
        media, peor = ms(tiempos)
        print(f"Tamaño de análisis {tam}: media {media:.0f} ms, peor {peor:.0f} ms "
              f"(máximo {1000 / media:.1f} análisis por segundo)")


def cpu():
    try:
        import psutil
    except ImportError:
        return
    print(f"\nUso de CPU ahora: {psutil.cpu_percent(interval=1.0):.0f} %")


if __name__ == "__main__":
    print("Fuente:", FUENTE or f"cámara {INDICE}")
    c = captura()
    if c is not None:
        rojo(c)
        yolo(c)
    cpu()
    print("\nFin de la medición.")