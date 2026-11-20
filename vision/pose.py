"""Reglas de postura y movimiento sobre puntos clave COCO (sin dependencias).

Mareo: la cabeza cae (hacia adelante o abajo) o se inclina hacia un lado
respecto de su posición calibrada y se mantiene un instante.
Movimiento brusco: velocidad media de munecas u hombros en una ventana corta.
"""
import math
from collections import deque
from statistics import median

CABEZA = (0, 1, 2, 3, 4)  # nariz, ojos, orejas
HOMBRO_I, HOMBRO_D, MUNECA_I, MUNECA_D = 5, 6, 9, 10
MAREO = "posible_mareo"
MOVIMIENTO = "movimiento_brusco"


class Detector:
    def __init__(self, calibracion=5.0, delta_caida=0.20, segundos_caida=1.5,
                 velocidad=6.0, segundos_movimiento=1.5, conf_min=0.5,
                 delta_lateral=0.30, segundos_lateral=None):
        self.calibracion = calibracion
        self.delta_caida = delta_caida
        self.segundos_caida = segundos_caida
        self.velocidad = velocidad
        self.segundos_movimiento = segundos_movimiento
        self.conf_min = conf_min
        # Inclinación lateral de la cabeza, en anchos de hombros. 0 la desactiva.
        self.delta_lateral = delta_lateral
        self.segundos_lateral = (
            segundos_caida if segundos_lateral is None else segundos_lateral
        )
        self.reiniciar_calibracion()

    def reiniciar_calibracion(self):
        self.base = None
        self.base_lateral = None
        self._inicio = None
        self._muestras = []
        self._muestras_lateral = []
        self.sin_persona()

    def sin_persona(self):
        self._desde_caida = None
        self._desde_lateral = None
        self._previo = None
        self._ventana = deque()
        self._recientes = deque(maxlen=5)
        self._recientes_lateral = deque(maxlen=5)
        self.caida = None
        self.lateral = None
        self.velocidad_actual = None
        self.confianza = 0.0

    @property
    def calibrado(self):
        return self.base is not None

    def _ok(self, conf, *indices):
        return all(conf[i] >= self.conf_min for i in indices)

    def _cabeza(self, xy, conf):
        puntos = [xy[i] for i in CABEZA if conf[i] >= self.conf_min]
        if not puntos:
            return None, None
        return (sum(p[0] for p in puntos) / len(puntos),
                sum(p[1] for p in puntos) / len(puntos))

    def _sostenido(self, exceso, t, atributo, segundos, activos, evento):
        if exceso:
            if getattr(self, atributo) is None:
                setattr(self, atributo, t)
            if t - getattr(self, atributo) >= segundos:
                activos.add(evento)
        else:
            setattr(self, atributo, None)

    def actualizar(self, t, xy, conf):
        """Devuelve el conjunto de eventos activos en este instante."""
        activos = set()
        ancho = None
        if self._ok(conf, HOMBRO_I, HOMBRO_D):
            ancho = math.dist(xy[HOMBRO_I], xy[HOMBRO_D])
            if ancho < 1e-6:
                ancho = None

        if ancho is None:
            self.caida = None
            self.lateral = None
            self._desde_caida = None
            self._desde_lateral = None
            self._recientes.clear()
            self._recientes_lateral.clear()
        else:
            hombros_x = (xy[HOMBRO_I][0] + xy[HOMBRO_D][0]) / 2
            hombros_y = (xy[HOMBRO_I][1] + xy[HOMBRO_D][1]) / 2
            cabeza_x, cabeza_y = self._cabeza(xy, conf)
            exceso = False
            exceso_lateral = False
            if cabeza_y is not None:
                self.caida = (cabeza_y - hombros_y) / ancho
                self.lateral = (cabeza_x - hombros_x) / ancho
                self._recientes.append(self.caida)
                self._recientes_lateral.append(self.lateral)
                suave = median(self._recientes)
                suave_lateral = median(self._recientes_lateral)
                visibles = [conf[i] for i in CABEZA if conf[i] >= self.conf_min]
                self.confianza = (
                    conf[HOMBRO_I] + conf[HOMBRO_D] + sum(visibles) / len(visibles)
                ) / 3
                if self.base is None:
                    if self._inicio is None:
                        self._inicio = t
                    self._muestras.append(self.caida)
                    self._muestras_lateral.append(self.lateral)
                    if t - self._inicio >= self.calibracion and len(self._muestras) >= 5:
                        self.base = median(self._muestras)
                        self.base_lateral = median(self._muestras_lateral)
                else:
                    exceso = suave - self.base > self.delta_caida
                    if self.delta_lateral > 0:
                        exceso_lateral = (
                            abs(suave_lateral - self.base_lateral) > self.delta_lateral
                        )
            elif self.base is not None:
                # La cabeza desapareció con los hombros visibles: cabeza caída.
                self.caida = self.base + 2 * self.delta_caida
                self.confianza = (conf[HOMBRO_I] + conf[HOMBRO_D]) / 2
                exceso = True

            self._sostenido(exceso, t, "_desde_caida", self.segundos_caida,
                            activos, MAREO)
            self._sostenido(exceso_lateral, t, "_desde_lateral",
                            self.segundos_lateral, activos, MAREO)

        # Movimiento brusco: velocidad de munecas u hombros, en anchos de
        # hombros por segundo. Sin munecas visibles se usan solo los hombros.
        if ancho is not None:
            munecas = self._ok(conf, MUNECA_I, MUNECA_D)
            actual = (xy[MUNECA_I], xy[MUNECA_D], xy[HOMBRO_I], xy[HOMBRO_D])
            if self._previo is not None:
                t0, anterior = self._previo
                dt = t - t0
                if dt > 0:
                    v = (
                        math.dist(actual[2], anterior[2])
                        + math.dist(actual[3], anterior[3])
                    ) / 2 / ancho / dt
                    if munecas:
                        vm = (
                            math.dist(actual[0], anterior[0])
                            + math.dist(actual[1], anterior[1])
                        ) / 2 / ancho / dt
                        v = max(v, vm)
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