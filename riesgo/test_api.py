from django.test import TestCase, override_settings
from django.urls import reverse

from pacientes.models import Estacion, Paciente, Sesion

from .models import Alerta, EventoVisual
from .services import crear_regla

TOKEN = {"HTTP_X_VISION_TOKEN": "clave-de-prueba"}


@override_settings(VISION_TOKEN="clave-de-prueba")
class ApiVisionTests(TestCase):
    def setUp(self):
        crear_regla("hemorragia", 90, 60)
        self.estacion = Estacion.objects.create(codigo="EST-07", sala="Sala A")
        paciente = Paciente.objects.create(codigo="PAC-007")
        self.sesion = Sesion.objects.create(paciente=paciente, estacion=self.estacion)
        self.url_evento = reverse("riesgo:evento")
        self.url_senal = reverse("riesgo:senal")

    def enviar(self, valor=95, identificador="ev-1", **extra):
        cuerpo = {
            "identificador": identificador, "estacion": "EST-07",
            "clase_evento": "hemorragia", "valor": valor, "camara": "CAM-07",
        }
        cuerpo.update(extra)
        return self.client.post(
            self.url_evento, cuerpo, content_type="application/json", **TOKEN
        )

    def test_sin_token_da_401(self):
        r = self.client.post(self.url_evento, {}, content_type="application/json")
        self.assertEqual(r.status_code, 401)

    def test_token_incorrecto_da_401(self):
        r = self.client.post(
            self.url_senal, {"estacion": "EST-07"},
            content_type="application/json", HTTP_X_VISION_TOKEN="mala",
        )
        self.assertEqual(r.status_code, 401)

    def test_senal_actualiza_la_estacion(self):
        r = self.client.post(
            self.url_senal, {"estacion": "EST-07"},
            content_type="application/json", **TOKEN,
        )
        self.assertEqual(r.status_code, 200)
        self.estacion.refresh_from_db()
        self.assertIsNotNone(self.estacion.ultima_senal)

    def test_senal_de_estacion_inexistente_da_404(self):
        r = self.client.post(
            self.url_senal, {"estacion": "EST-99"},
            content_type="application/json", **TOKEN,
        )
        self.assertEqual(r.status_code, 404)

    def test_evento_alto_crea_alerta_critica(self):
        r = self.enviar(valor=95)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["estado"], "critica")
        self.assertEqual(Alerta.objects.count(), 1)
        self.assertEqual(EventoVisual.objects.get().camara, "CAM-07")

    def test_evento_bajo_no_es_critico(self):
        r = self.enviar(valor=70)
        self.assertEqual(r.json()["estado"], "normal")

    def test_repetir_el_identificador_no_duplica(self):
        self.enviar(identificador="ev-9")
        r = self.enviar(identificador="ev-9")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(EventoVisual.objects.count(), 1)

    def test_estacion_sin_sesion_da_409(self):
        self.sesion.fin = self.sesion.inicio
        self.sesion.save()
        self.assertEqual(self.enviar().status_code, 409)

    def test_valor_fuera_de_rango_da_400(self):
        self.assertEqual(self.enviar(valor=150).status_code, 400)

    def test_faltan_campos_da_400(self):
        r = self.client.post(
            self.url_evento, {"estacion": "EST-07"},
            content_type="application/json", **TOKEN,
        )
        self.assertEqual(r.status_code, 400)

    def test_get_no_esta_permitido(self):
        self.assertEqual(self.client.get(self.url_evento, **TOKEN).status_code, 405)