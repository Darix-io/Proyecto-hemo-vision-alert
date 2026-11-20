"""Detección de color rojo en cara, boca, mentón y pecho (simulación de sangrado).

Idea: no se busca "rojo", se busca rojo NUEVO respecto a la apariencia del paciente.
Durante la calibración se aprende dónde hay rojo (camiseta, labial) y después solo
cuenta el rojo que aparece fuera de ese mapa.
"""
from statistics import median

import cv2
import numpy as np

NARIZ, HOMBRO_I, HOMBRO_D, CADERA_I, CADERA_D = 0, 5, 6, 11, 12
HEMORRAGIA = "hemorragia"
REJILLA = 24  # cada zona se reduce a una rejilla de 24 x 24 celdas


def mascara_roja(bgr, r_min=60, razon=0.45, dif_min=50):
    """Rojo por proporción (verde bajo respecto al rojo). Acepta rojos vivos, oscuros y apagados."""
    b = bgr[..., 0].astype(np.int16)
    g = bgr[..., 1].astype(np.int16)
    r = bgr[..., 2].astype(np.int16)
    ok = (r >= r_min) & (g <= r * razon) & ((r - g) >= dif_min) & (b <= r * 0.85)
    return ok.astype(np.uint8) * 255


def zonas(xy, conf, forma, conf_min=0.5):
    """Rectángulos (x1, y1, x2, y2) de pecho y rostro (frente, nariz, boca y mentón)."""
    alto, ancho = forma[:2]
    if min(conf[HOMBRO_I], conf[HOMBRO_D]) < conf_min:
        return []
    hi, hd = xy[HOMBRO_I], xy[HOMBRO_D]
    separacion = abs(hd[0] - hi[0])
    if separacion < 10:
        return []
    cx = (hi[0] + hd[0]) / 2
    hombros_y = (hi[1] + hd[1]) / 2
    base_pecho = hombros_y + separacion * 1.0
    if min(conf[CADERA_I], conf[CADERA_D]) >= conf_min:
        caderas_y = (xy[CADERA_I][1] + xy[CADERA_D][1]) / 2
        if caderas_y > hombros_y + separacion * 0.3:
            base_pecho = min(base_pecho, caderas_y)
    pecho = (cx - separacion * 0.6, hombros_y, cx + separacion * 0.6, base_pecho)
    if conf[NARIZ] >= conf_min:
        fx, fy = xy[NARIZ]
    else:  # nariz tapada: se estima la cara sobre los hombros
        fx, fy = cx, hombros_y - separacion * 0.45
    rostro = (
        fx - separacion * 0.45, fy - separacion * 0.5,
        fx + separacion * 0.45, fy + separacion * 0.95,
    )
    salida = []
    for x1, y1, x2, y2 in (pecho, rostro):
        x1, y1 = max(int(x1), 0), max(int(y1), 0)
        x2, y2 = min(int(x2), ancho), min(int(y2), alto)
        if x2 - x1 > 5 and y2 - y1 > 5:
            salida.append((x1, y1, x2, y2))
    return salida


def fraccion_roja(bgr, rects):
    """Mayor proporción de rojo entre las zonas (la cara pequeña pesa tanto como el pecho)."""
    mejor = 0.0
    for x1, y1, x2, y2 in rects:
        zona = bgr[y1:y2, x1:x2]
        if zona.size == 0:
            continue
        m = mascara_roja(zona)
        mejor = max(mejor, int(np.count_nonzero(m)) / m.size)
    return mejor


def rejillas_rojas(bgr, rects):
    """Una rejilla por zona: fracción de rojo en cada celda (0 a 1)."""
    salida = []
    for x1, y1, x2, y2 in rects:
        zona = bgr[y1:y2, x1:x2]
        if zona.size == 0:
            salida.append(np.zeros((REJILLA, REJILLA), np.float32))
            continue
        m = (mascara_roja(zona) > 0).astype(np.float32)
        salida.append(cv2.resize(m, (REJILLA, REJILLA), interpolation=cv2.INTER_AREA))
    return salida


def resaltar(vista, rects):
    """Pinta de amarillo los píxeles que el detector toma como rojos."""
    for x1, y1, x2, y2 in rects:
        zona = vista[y1:y2, x1:x2]
        if zona.size:
            zona[mascara_roja(zona) > 0] = (0, 255, 255)


class DetectorSangre:
    def __init__(self, calibracion=3.0, delta=0.03, segundos=0.6, absoluto=0.30,
                 base_baja=0.10):
        self.calibracion = calibracion
        self.delta = delta
        self.segundos = segundos
        self.absoluto = absoluto
        self.base_baja = base_baja  # el umbral absoluto solo vale si la base es menor
        self.reiniciar()

    def reiniciar(self):
        self.base = None
        self._inicio = None
        self._muestras = []
        self._desde = None
        self.fraccion = None
        self._suma = None      # suma de rejillas durante la calibración
        self._cuadros = 0
        self._mapa = None      # mapa del rojo que ya tenía el paciente

    @property
    def calibrado(self):
        return self.base is not None

    def medir(self, bgr, rects):
        """Proporción de rojo para actualizar().

        En la calibración aprende el mapa de rojo del paciente y devuelve la proporción
        normal. Ya calibrado devuelve base + rojo NUEVO (el rojo del mapa no suma)."""
        if not rects:
            return None
        rejillas = rejillas_rojas(bgr, rects)
        if self.base is None:
            if self._suma is None or len(self._suma) != len(rejillas):
                self._suma = [np.zeros_like(r) for r in rejillas]
                self._cuadros = 0
            for s, r in zip(self._suma, rejillas):
                s += r
            self._cuadros += 1
            return fraccion_roja(bgr, rects)
        if self._mapa is None and self._suma is not None:
            nucleo = np.ones((3, 3), np.uint8)
            self._mapa = [
                cv2.dilate(((s / max(self._cuadros, 1)) >= 0.5).astype(np.uint8), nucleo) > 0
                for s in self._suma
            ]
        if self._mapa is None or len(self._mapa) != len(rejillas):
            return fraccion_roja(bgr, rects)  # zonas distintas a las calibradas
        nuevo = 0.0
        for mapa, rej in zip(self._mapa, rejillas):
            rojo_nuevo = (rej >= 0.5) & ~mapa
            nuevo = max(nuevo, float(np.count_nonzero(rojo_nuevo)) / rojo_nuevo.size)
        return self.base + nuevo

    def actualizar(self, t, fraccion):
        """fraccion: proporción de rojo, o None si no se ve a la persona. True si hay alerta."""
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
        absoluto = self.base < self.base_baja and fraccion >= self.absoluto
        if absoluto or fraccion - self.base > self.delta:
            if self._desde is None:
                self._desde = t
            return t - self._desde >= self.segundos
        self._desde = None
        return False