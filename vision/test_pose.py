import unittest

from pose import MAREO, MOVIMIENTO, Detector

PASO = 0.2
T0 = 1000.0


def pose(caida=-0.5, mun_i=(100, 300), mun_d=(200, 300), conf=0.9):
    xy = [(0, 0)] * 17
    xy[5], xy[6] = (100, 200), (200, 200)  # hombros: ancho 100
    xy[0] = (150, 200 + caida * 100)
    xy[9], xy[10] = mun_i, mun_d
    return xy, [conf] * 17


def correr(det, t_ini, duracion, f):
    salida = []
    for i in range(int(round(duracion / PASO)) + 1):
        xy, conf = f(i)
        salida.append((i * PASO, det.actualizar(t_ini + i * PASO, xy, conf)))
    return salida


def calibrar(det, caida=-0.5):
    correr(det, T0, 6.0, lambda i: pose(caida))
    assert det.calibrado
    return T0 + 6.2


class DetectorTests(unittest.TestCase):
    def test_calibra_y_no_dispara_en_reposo(self):
        det = Detector()
        res = correr(det, T0, 8.0, lambda i: pose())
        self.assertTrue(det.calibrado)
        self.assertAlmostEqual(det.base, -0.5, places=2)
        self.assertFalse(any(a for _, a in res))

    def test_mareo_exige_duracion(self):
        det = Detector()
        t = calibrar(det)
        res = correr(det, t, 2.6, lambda i: pose(-0.1))
        self.assertFalse(any(MAREO in a for e, a in res if e < 1.8))
        self.assertTrue(any(MAREO in a for _, a in res))

    def test_un_pico_corto_no_es_mareo(self):
        det = Detector()
        t = calibrar(det)
        res = correr(det, t, 3.0, lambda i: pose(-0.1 if i in (3, 4) else -0.5))
        self.assertFalse(any(MAREO in a for _, a in res))

    def test_movimiento_sostenido_dispara(self):
        det = Detector()
        t = calibrar(det)
        res = correr(
            det, t, 2.4,
            lambda i: pose(mun_i=(100 + 150 * (i % 2), 300), mun_d=(200 - 150 * (i % 2), 300)),
        )
        self.assertTrue(any(MOVIMIENTO in a for _, a in res))

    def test_un_pico_de_velocidad_aislado_no_cuenta(self):
        det = Detector()
        t = calibrar(det)
        res = correr(
            det, t, 2.4,
            lambda i: pose(mun_i=(250, 300)) if i == 5 else pose(),
        )
        self.assertFalse(any(MOVIMIENTO in a for _, a in res))

    def test_puntos_con_poca_confianza_no_cuentan(self):
        det = Detector()
        t = calibrar(det)
        res = correr(det, t, 3.0, lambda i: pose(-0.1, conf=0.2))
        self.assertFalse(any(a for _, a in res))
        self.assertIsNone(det.caida)

    def test_una_postura_inclinada_de_base_no_dispara(self):
        det = Detector()
        t = calibrar(det, caida=-0.2)
        res = correr(det, t, 4.0, lambda i: pose(-0.2))
        self.assertFalse(any(a for _, a in res))


if __name__ == "__main__":
    unittest.main()
