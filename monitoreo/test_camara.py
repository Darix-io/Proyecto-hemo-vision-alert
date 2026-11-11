from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from pacientes.models import Estacion, Paciente, Sesion
from riesgo.models import Alerta, ReglaRiesgo


@override_settings(
    VISION_STREAM_URL="http://127.0.0.1:8001/video", VISION_STREAM_ESTACION="EST-07"
)
class CamaraTests(TestCase):
    def setUp(self):
        usuario = get_user_model().objects.create_user(
            username="medico", password="clave-de-prueba-123"
        )
        self.client.force_login(usuario)
        regla = ReglaRiesgo.objects.create(
            clase_evento="hemorragia", umbral=60, ventana_segundos=60
        )
        self.alertas = {}
        for codigo in ("EST-07", "EST-08"):
            estacion = Estacion.objects.create(
                codigo=codigo, sala="Sala A", ultima_senal=timezone.now()
            )
            paciente = Paciente.objects.create(codigo=f"P-{codigo}")
            sesion = Sesion.objects.create(paciente=paciente, estacion=estacion)
            self.alertas[codigo] = Alerta.objects.create(
                sesion=sesion, clase_evento="hemorragia", estado="critica", regla=regla
            )

    def test_el_dashboard_muestra_la_camara_en_vivo(self):
        r = self.client.get(reverse("monitoreo:dashboard"))
        self.assertContains(r, "Cámara en vivo")
        self.assertContains(r, "http://127.0.0.1:8001/video")

    def test_el_detalle_de_la_estacion_con_camara_muestra_el_video(self):
        url = reverse("monitoreo:detalle_alerta", args=[self.alertas["EST-07"].pk])
        self.assertContains(self.client.get(url), "http://127.0.0.1:8001/video")

    def test_otra_estacion_sigue_con_evidencia_simulada(self):
        url = reverse("monitoreo:detalle_alerta", args=[self.alertas["EST-08"].pk])
        r = self.client.get(url)
        self.assertContains(r, "imagen simulada")
        self.assertNotContains(r, "http://127.0.0.1:8001/video")