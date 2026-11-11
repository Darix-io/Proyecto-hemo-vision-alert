"""Reglas de postura y movimiento sobre puntos clave COCO (sin dependencias)."""
import math
from collections import deque
from statistics import median

NARIZ, HOMBRO_I, HOMBRO_D, MUNECA_I, MUNECA_D = 0, 5, 6, 9, 10
MAREO = "posible_mareo"
MOVIMIENTO = "movimiento_brusco"


class Detector:
    def __init__(self, calibracion=5.0, delta_caida=0.25, segundos_caida=2.0,
                 velocidad=6.0, segundos_movimiento=1.5, conf_min=0.5):
        self.calibracion = calibracion
        self.delta_caida = delta_caida
        self.segundos_caida = segundos_caida
        self.velocidad = velocidad
        self.segundos_movimiento = segundos_movimiento
        self.conf_min = conf_min
        self.reiniciar_calibracion()

    def reiniciar_calibracion(self):
        self.base = None
        self._inicio = None
        self._muestras = []
        self.sin_persona()

    def sin_persona(self):
        self._desde_caida = None
        self._previo = None
        self._ventana = deque()
        self.caida = None
        self.velocidad_actual = None
        self.confianza = 0.0

    @property
    def calibrado(self):
        return self.base is not None

    def _ok(self, conf, *indices):
        return all(conf[i] >= self.conf_min for i in indices)

    def actualizar(self, t, xy, conf):
        """Devuelve el conjunto de eventos activos en este instante."""
        activos = set()
        ancho = None
        if self._ok(conf, HOMBRO_I, HOMBRO_D):
            ancho = math.dist(xy[HOMBRO_I], xy[HOMBRO_D])
            if ancho < 1e-6:
                ancho = None

        # Cabeza caída: cambio respecto a la postura calibrada.
        if ancho is not None and self._ok(conf, NARIZ):
            hombros_y = (xy[HOMBRO_I][1] + xy[HOMBRO_D][1]) / 2
            self.caida = (xy[NARIZ][1] - hombros_y) / ancho
            self.confianza = (
                conf[NARIZ] + conf[HOMBRO_I] + conf[HOMBRO_D]
            ) / 3
            if self.base is None:
                if self._inicio is None:
                    self._inicio = t
                self._muestras.append(self.caida)
                if t - self._inicio >= self.calibracion and len(self._muestras) >= 5:
                    self.base = median(self._muestras)
            elif self.caida - self.base > self.delta_caida:
                if self._desde_caida is None:
                    self._desde_caida = t
                if t - self._desde_caida >= self.segundos_caida:
                    activos.add(MAREO)
            else:
                self._desde_caida = None
        else:
            self.caida = None
            self._desde_caida = None

        # Movimiento brusco: velocidad de muñecas en anchos de hombros por segundo.
        if ancho is not None and self._ok(conf, MUNECA_I, MUNECA_D):
            actual = (xy[MUNECA_I], xy[MUNECA_D])
            if self._previo is not None:
                t0, anterior = self._previo
                dt = t - t0
                if dt > 0:
                    v = (
                        math.dist(actual[0], anterior[0])
                        + math.dist(actual[1], anterior[1])
                    ) / 2 / ancho / dt
                    self.velocidad_actual = v
                    self._ventana.append((t, v))
            self._previo = (t, actual)
            while self._ventana and self._ventana[0][0] < t - self.segundos_movimiento:
                self._ventana.popleft()
            if (
                len(self._ventana) >= 3
                and t - self._ventana[0][0] >= self.segundos_movimiento * 0.8
                and sum(v for _, v in self._ventana) / len(self._ventana) >= self.velocidad
            ):
                activos.add(MOVIMIENTO)
        else:
            self._previo = None
            self._ventana.clear()
            self.velocidad_actual = None
        return activos
