import base64
import tempfile

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from pacientes.models import Estacion, Paciente, Sesion

from .models import EventoVisual
from .services import crear_regla

TOKEN = {"HTTP_X_VISION_TOKEN": "clave-de-prueba"}
JPEG = base64.b64encode(b"\xff\xd8\xff\xe0" + b"0" * 64).decode()
TEXTO = base64.b64encode(b"esto no es una imagen").decode()
MEDIA = tempfile.mkdtemp()


@override_settings(VISION_TOKEN="clave-de-prueba", MEDIA_ROOT=MEDIA)
class CapturaTests(TestCase):
    def setUp(self):
        crear_regla("hemorragia", 60, 60)
        estacion = Estacion.objects.create(codigo="EST-07", sala="Sala A")
        paciente = Paciente.objects.create(codigo="PAC-007")
        Sesion.objects.create(paciente=paciente, estacion=estacion)
        self.usuario = get_user_model().objects.create_user(
            username="medico", password="clave-de-prueba-123"
        )

    def enviar(self, captura=JPEG, ident="c1"):
        return self.client.post(
            reverse("riesgo:evento"),
            {"identificador": ident, "estacion": "EST-07", "clase_evento": "hemorragia",
             "valor": 95, "camara": "CAM-07", "captura": captura},
            content_type="application/json", **TOKEN,
        )

    def test_guarda_la_captura_del_evento(self):
        self.assertEqual(self.enviar().status_code, 201)
        self.assertTrue(EventoVisual.objects.get().captura)

    def test_una_captura_invalida_se_ignora_pero_el_evento_se_guarda(self):
        self.assertEqual(self.enviar(TEXTO).status_code, 201)
        self.assertFalse(EventoVisual.objects.get().captura)

    def test_el_detalle_y_el_informe_muestran_la_captura(self):
        alerta = self.enviar().json()["alerta"]
        self.client.force_login(self.usuario)
        detalle = self.client.get(reverse("monitoreo:detalle_alerta", args=[alerta]))
        self.assertContains(detalle, "Captura del evento")
        informe = self.client.get(reverse("monitoreo:informe_alerta", args=[alerta]))
        self.assertContains(informe, "Informe de evento")
        self.assertContains(informe, "EST-07")
