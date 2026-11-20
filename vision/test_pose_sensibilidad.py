import unittest
from pose import Detector, MAREO, MOVIMIENTO


def cuerpo(cx=0.0, cy=0.0, cabeza_dx=0.0, cabeza_dy=0.0, mun=(0.0, 0.0)):
    """17 puntos COCO. Hombros ancho 100, cabeza 90 por encima de los hombros."""
    xy = [(0.0, 0.0)] * 17
    xy = list(xy)
    for i in (0, 1, 2, 3, 4):
        xy[i] = (cx + cabeza_dx, cy - 90 + cabeza_dy)
    xy[5] = (cx - 50, cy)
    xy[6] = (cx + 50, cy)
    xy[9] = (cx - 80 + mun[0], cy + 150 + mun[1])
    xy[10] = (cx + 80 + mun[0], cy + 150 + mun[1])
    return xy, [0.9] * 17


def correr(det, fps, segundos, fabrica):
    """Avanza el reloj del detector; devuelve {evento: segundos hasta el primero}."""
    eventos = {}
    t0 = getattr(det, "_reloj", 0.0)
    n = int(segundos * fps)
    for k in range(n):
        t = t0 + k / fps
        xy, conf = fabrica(k, t - t0)
        for e in det.actualizar(t, xy, conf):
            eventos.setdefault(e, t - t0)
    det._reloj = t0 + n / fps
    return eventos


def calibrado(**kw):
    d = Detector(delta_caida=0.12, segundos_caida=0.6, velocidad=3.5,
                 segundos_movimiento=0.8, **kw)
    correr(d, 7, 6, lambda k, t: cuerpo())
    assert d.calibrado
    return d


class Sensibilidad(unittest.TestCase):
    def test_quieto_no_alerta(self):
        d = calibrado()
        self.assertEqual(correr(d, 7, 60, lambda k, t: cuerpo(
            cabeza_dx=((k % 3) - 1) * 1.5, cabeza_dy=((k % 2) - 0.5) * 2)), {})

    def test_cabeza_cae_rapido(self):
        d = calibrado()
        ev = correr(d, 7, 3, lambda k, t: cuerpo(cabeza_dy=25))
        self.assertIn(MAREO, ev)
        self.assertLessEqual(ev[MAREO], 1.0)

    def test_inclina_a_un_lado(self):
        d = calibrado()
        ev = correr(d, 7, 3, lambda k, t: cuerpo(cabeza_dx=40))
        self.assertIn(MAREO, ev)
        self.assertLessEqual(ev[MAREO], 1.0)

    def test_inclina_al_otro_lado(self):
        d = calibrado()
        self.assertIn(MAREO, correr(d, 7, 3, lambda k, t: cuerpo(cabeza_dx=-40)))

    def test_gesto_corto_no_alerta(self):
        d = calibrado()
        ev = correr(d, 7, 4, lambda k, t: cuerpo(cabeza_dx=40 if 7 <= k < 9 else 0))
        self.assertNotIn(MAREO, ev)

    def test_lateral_desactivable(self):
        d = Detector(delta_caida=0.12, segundos_caida=0.6, delta_lateral=0)
        correr(d, 7, 6, lambda k, t: cuerpo())
        self.assertNotIn(MAREO, correr(d, 7, 3, lambda k, t: cuerpo(cabeza_dx=40)))

    def test_brazos_rapidos(self):
        d = calibrado()
        ev = correr(d, 7, 3, lambda k, t: cuerpo(mun=((-1) ** k * 45, 0)))
        self.assertIn(MOVIMIENTO, ev)
        self.assertLessEqual(ev[MOVIMIENTO], 1.5)

    def test_cuerpo_rapido_sin_munecas(self):
        d = calibrado()

        def f(k, t):
            xy, conf = cuerpo(cx=(-1) ** k * 30)
            conf[9] = conf[10] = 0.1
            return xy, conf
        self.assertIn(MOVIMIENTO, correr(d, 7, 3, f))

    def test_gesto_lento_no_alerta(self):
        d = calibrado()
        self.assertNotIn(MOVIMIENTO, correr(d, 7, 10,
                         lambda k, t: cuerpo(mun=(10 * (k % 2), 0))))


if __name__ == "__main__":
    unittest.main()