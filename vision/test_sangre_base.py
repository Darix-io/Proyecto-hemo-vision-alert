"""Pruebas de la línea base del paciente: camiseta roja y labial no deben alertar."""
import unittest

import numpy as np

from sangre import DetectorSangre

PASO = 0.2
T0 = 1000.0
ROJO = (0, 0, 210)      # BGR
PIEL = (110, 140, 190)
RECTS = [(0, 0, 200, 200), (200, 0, 300, 100)]  # pecho y rostro


def cuadro(camiseta=False, labial=False, mancha=None):
    img = np.zeros((240, 320, 3), np.uint8)
    img[:] = PIEL
    if camiseta:
        img[:, :200] = ROJO              # toda la zona del pecho en rojo
    if labial:
        img[60:75, 230:270] = ROJO       # labios en la zona del rostro
    if mancha:
        x1, y1, x2, y2 = mancha
        img[y1:y2, x1:x2] = ROJO
    return img


def corre(det, t_ini, seg, hacer):
    res = []
    for i in range(int(round(seg / PASO)) + 1):
        t = t_ini + i * PASO
        res.append(det.actualizar(t, det.medir(hacer(i), RECTS)))
    return res


class LineaBaseTests(unittest.TestCase):
    def calibra(self, **kw):
        det = DetectorSangre(delta=0.06)
        corre(det, T0, 4.0, lambda i: cuadro(**kw))
        self.assertTrue(det.calibrado)
        return det

    def test_camiseta_roja_de_base_no_dispara(self):
        det = self.calibra(camiseta=True)
        res = corre(det, T0 + 4.2, 6.0, lambda i: cuadro(camiseta=True))
        self.assertFalse(any(res))

    def test_labial_rojo_de_base_no_dispara(self):
        det = self.calibra(labial=True)
        res = corre(det, T0 + 4.2, 6.0, lambda i: cuadro(labial=True))
        self.assertFalse(any(res))

    def test_rojo_nuevo_con_camiseta_roja_dispara(self):
        det = self.calibra(camiseta=True)
        res = corre(det, T0 + 4.2, 3.0,
                    lambda i: cuadro(camiseta=True, mancha=(210, 10, 290, 90)))
        self.assertTrue(any(res))

    def test_rojo_nuevo_con_labial_dispara(self):
        det = self.calibra(labial=True)
        res = corre(det, T0 + 4.2, 3.0, lambda i: cuadro(labial=True, mancha=(20, 20, 120, 120)))
        self.assertTrue(any(res))

    def test_sin_base_roja_un_objeto_rojo_dispara(self):
        det = self.calibra()
        res = corre(det, T0 + 4.2, 3.0, lambda i: cuadro(mancha=(20, 20, 120, 120)))
        self.assertTrue(any(res))

    def test_un_destello_no_dispara(self):
        det = self.calibra(camiseta=True)
        res = corre(det, T0 + 4.2, 3.0,
                    lambda i: cuadro(camiseta=True, mancha=(210, 10, 290, 90)) if i in (3, 4)
                    else cuadro(camiseta=True))
        self.assertFalse(any(res))

    def test_absoluto_no_aplica_con_base_alta(self):
        det = DetectorSangre()
        for i in range(25):
            det.actualizar(T0 + i * PASO, 0.5)
        self.assertGreater(det.base, 0.1)
        res = [det.actualizar(T0 + 6 + i * PASO, 0.5) for i in range(15)]
        self.assertFalse(any(res))

    def test_absoluto_sigue_con_base_baja(self):
        det = DetectorSangre()
        for i in range(25):
            det.actualizar(T0 + i * PASO, 0.02)
        res = [det.actualizar(T0 + 6 + i * PASO, 0.4) for i in range(15)]
        self.assertTrue(any(res))


if __name__ == "__main__":
    unittest.main()