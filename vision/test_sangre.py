import unittest

import numpy as np

from sangre import DetectorSangre, fraccion_roja, mascara_roja, zonas

PASO = 0.2
T0 = 1000.0


def color(bgr):
    img = np.zeros((10, 10, 3), np.uint8)
    img[:] = bgr
    return int(mascara_roja(img).sum() // 255)


def corre(det, t_ini, seg, valor):
    return [det.actualizar(t_ini + i * PASO, valor(i)) for i in range(int(round(seg / PASO)) + 1)]


class SangreTests(unittest.TestCase):
    def test_mascara_acepta_rojos_vivos_oscuros_apagados_y_rosados(self):
        for bgr in [(0, 0, 220), (10, 10, 70), (60, 60, 150), (150, 60, 220)]:
            self.assertEqual(color(bgr), 100, bgr)

    def test_mascara_rechaza_azul_piel_y_gris(self):
        for bgr in [(220, 60, 0), (120, 150, 200), (120, 120, 120), (30, 30, 30)]:
            self.assertEqual(color(bgr), 0, bgr)

    def test_fraccion_roja_toma_la_zona_mas_roja(self):
        img = np.zeros((100, 100, 3), np.uint8)
        img[:] = (200, 100, 50)
        img[:50, :] = (0, 0, 220)
        self.assertAlmostEqual(fraccion_roja(img, [(0, 0, 100, 100)]), 0.5, places=2)
        self.assertAlmostEqual(fraccion_roja(img, [(0, 0, 100, 50), (0, 50, 100, 100)]), 1.0, places=2)

    def test_zonas_vacias_si_no_se_ven_hombros(self):
        self.assertEqual(zonas([(0, 0)] * 17, [0.1] * 17, (480, 640, 3)), [])

    def test_zonas_con_la_nariz_tapada_siguen_existiendo(self):
        xy = [(0, 0)] * 17
        xy[5], xy[6] = (250, 250), (390, 250)
        conf = [0.9] * 17
        conf[0] = 0.05
        self.assertEqual(len(zonas(xy, conf, (480, 640, 3))), 2)

    def test_el_rostro_incluye_boca_y_menton(self):
        xy = [(0, 0)] * 17
        xy[0], xy[5], xy[6] = (320, 150), (250, 250), (390, 250)
        rects = zonas(xy, [0.9] * 17, (480, 640, 3))
        self.assertEqual(len(rects), 2)
        self.assertGreaterEqual(rects[1][3], 150 + 112)

    def test_calibra_y_no_dispara_en_reposo(self):
        det = DetectorSangre()
        res = corre(det, T0, 6.0, lambda i: 0.02)
        self.assertTrue(det.calibrado)
        self.assertFalse(any(res))

    def test_rojo_sostenido_dispara(self):
        det = DetectorSangre()
        corre(det, T0, 4.0, lambda i: 0.02)
        self.assertTrue(any(corre(det, T0 + 4.2, 2.0, lambda i: 0.12)))

    def test_rojo_muy_alto_dispara_aunque_la_base_sea_alta(self):
        det = DetectorSangre()
        corre(det, T0, 4.0, lambda i: 0.28)
        self.assertTrue(any(corre(det, T0 + 4.2, 2.0, lambda i: 0.50)))

    def test_un_destello_no_dispara(self):
        det = DetectorSangre()
        corre(det, T0, 4.0, lambda i: 0.02)
        self.assertFalse(any(corre(det, T0 + 4.2, 3.0, lambda i: 0.30 if i == 4 else 0.02)))

    def test_sin_persona_no_dispara(self):
        det = DetectorSangre()
        corre(det, T0, 4.0, lambda i: 0.02)
        self.assertFalse(any(corre(det, T0 + 4.2, 3.0, lambda i: None)))


if __name__ == "__main__":
    unittest.main()
