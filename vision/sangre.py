"""Detección de color rojo en pecho y rostro (simulación de sangrado)."""
from statistics import median

import cv2
import numpy as np

NARIZ, HOMBRO_I, HOMBRO_D, CADERA_I, CADERA_D = 0, 5, 6, 11, 12
HEMORRAGIA = "hemorragia"


def mascara_roja(bgr, s_min=80, v_min=70):
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    bajo = cv2.inRange(hsv, (0, s_min, v_min), (10, 255, 255))
    alto = cv2.inRange(hsv, (160, s_min, v_min), (180, 255, 255))
    return cv2.bitwise_or(bajo, alto)

def zonas(xy, conf, forma, conf_min=0.5):
    """Devuelve rectángulos (x1, y1, x2, y2) de pecho y rostro, o [] si no se ven."""
    alto, ancho = forma[:2]
    if min(conf[HOMBRO_I], conf[HOMBRO_D], conf[NARIZ]) < conf_min:
        return []
    hi, hd, nariz = xy[HOMBRO_I], xy[HOMBRO_D], xy[NARIZ]
    separacion = abs(hd[0] - hi[0])
    if separacion < 10:
        return []
    cx = (hi[0] + hd[0]) / 2
    hombros_y = (hi[1] + hd[1]) / 2
    base_pecho = hombros_y + separacion * 1.0
    if min(conf[CADERA_I], conf[CADERA_D]) >= conf_min:
        caderas_y = (xy[CADERA_I][1] + xy[CADERA_D][1]) / 2
        # Solo se usa la cadera si queda claramente por debajo de los hombros.
        if caderas_y > hombros_y + separacion * 0.3:
            base_pecho = min(base_pecho, caderas_y)
    pecho = (cx - separacion * 0.5, hombros_y, cx + separacion * 0.5, base_pecho)
    rostro = (
        nariz[0] - separacion * 0.35, nariz[1] - separacion * 0.45,
        nariz[0] + separacion * 0.35, nariz[1] + separacion * 0.45,
    )
    salida = []
    for x1, y1, x2, y2 in (pecho, rostro):
        x1, y1 = max(int(x1), 0), max(int(y1), 0)
        x2, y2 = min(int(x2), ancho), min(int(y2), alto)
        if x2 - x1 > 5 and y2 - y1 > 5:
            salida.append((x1, y1, x2, y2))
    return salida


def fraccion_roja(bgr, rects):
    total = rojos = 0
    for x1, y1, x2, y2 in rects:
        zona = bgr[y1:y2, x1:x2]
        if zona.size == 0:
            continue
        m = mascara_roja(zona)
        rojos += int(np.count_nonzero(m))
        total += m.size
    return rojos / total if total else 0.0


class DetectorSangre:
    def __init__(self, calibracion=3.0, delta=0.06, segundos=1.5):
        self.calibracion = calibracion
        self.delta = delta
        self.segundos = segundos
        self.reiniciar()

    def reiniciar(self):
        self.base = None
        self._inicio = None
        self._muestras = []
        self._desde = None
        self.fraccion = None

    @property
    def calibrado(self):
        return self.base is not None

    def actualizar(self, t, fraccion):
        """fraccion: proporción de rojo en las zonas, o None si no se ven. Devuelve True si hay alerta."""
        self.fraccion = fraccion
        if fraccion is None:
            self._desde = None
            return False
        if self.base is None:
            if self._inicio is None:
                self._inicio = t
            self._muestras.append(fraccion)
            if t - self._inicio >= self.calibracion and len(self._muestras) >= 5:
                self.base = median(self._muestras)
            return False
        if fraccion - self.base > self.delta:
            if self._desde is None:
                self._desde = t
            return t - self._desde >= self.segundos
        self._desde = None
        return False
