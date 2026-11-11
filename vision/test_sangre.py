import unittest

import numpy as np

from sangre import DetectorSangre, fraccion_roja, mascara_roja, zonas

PASO = 0.2
T0 = 1000.0


def corre(det, t_ini, seg, valor):
    res = []
    for i in range(int(round(seg / PASO)) + 1):
        res.append(det.actualizar(t_ini + i * PASO, valor(i)))
    return res


class SangreTests(unittest.TestCase):
    def test_mascara_distingue_rojo_de_azul(self):
        rojo = np.zeros((10, 10, 3), np.uint8)
        rojo[:] = (0, 0, 220)      # BGR rojo
        azul = np.zeros((10, 10, 3), np.uint8)
        azul[:] = (220, 60, 0)     # BGR azul
        self.assertEqual(int(mascara_roja(rojo).sum() // 255), 100)
        self.assertEqual(int(mascara_roja(azul).sum()), 0)

    def test_fraccion_roja_de_una_zona(self):
        img = np.zeros((100, 100, 3), np.uint8)
        img[:] = (200, 100, 50)
        img[:, :50] = (0, 0, 220)
        self.assertAlmostEqual(fraccion_roja(img, [(0, 0, 100, 100)]), 0.5, places=2)

    def test_zonas_vacias_si_no_se_ven_hombros(self):
        xy = [(0, 0)] * 17
        self.assertEqual(zonas(xy, [0.1] * 17, (480, 640, 3)), [])

    def test_zonas_dentro_de_la_imagen(self):
        xy = [(0, 0)] * 17
        xy[0], xy[5], xy[6] = (320, 150), (250, 250), (390, 250)
        rects = zonas(xy, [0.9] * 17, (480, 640, 3))
        self.assertEqual(len(rects), 2)
        for x1, y1, x2, y2 in rects:
            self.assertTrue(0 <= x1 < x2 <= 640 and 0 <= y1 < y2 <= 480)

    def test_calibra_y_no_dispara_en_reposo(self):
        det = DetectorSangre()
        res = corre(det, T0, 6.0, lambda i: 0.02)
        self.assertTrue(det.calibrado)
        self.assertFalse(any(res))

    def test_rojo_sostenido_dispara(self):
        det = DetectorSangre()
        corre(det, T0, 4.0, lambda i: 0.02)
        res = corre(det, T0 + 4.2, 2.4, lambda i: 0.30)
        self.assertTrue(any(res))

    def test_un_destello_no_dispara(self):
        det = DetectorSangre()
        corre(det, T0, 4.0, lambda i: 0.02)
        res = corre(det, T0 + 4.2, 3.0, lambda i: 0.30 if i in (4, 5) else 0.02)
        self.assertFalse(any(res))

    def test_sin_persona_no_dispara(self):
        det = DetectorSangre()
        corre(det, T0, 4.0, lambda i: 0.02)
        res = corre(det, T0 + 4.2, 3.0, lambda i: None)
        self.assertFalse(any(res))


if __name__ == "__main__":
    unittest.main()
