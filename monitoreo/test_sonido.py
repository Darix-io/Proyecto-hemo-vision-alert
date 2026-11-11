from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from pacientes.models import Estacion, Paciente, Sesion
from riesgo.models import Alerta, ReglaRiesgo


class SonidoTests(TestCase):
    def setUp(self):
        usuario = get_user_model().objects.create_user(
            username="medico", password="clave-de-prueba-123"
        )
        self.client.force_login(usuario)
        regla = ReglaRiesgo.objects.create(
            clase_evento="posible_mareo", umbral=50, ventana_segundos=60
        )
        estacion = Estacion.objects.create(
            codigo="EST-07", sala="Sala A", ultima_senal=timezone.now()
        )
        paciente = Paciente.objects.create(codigo="PAC-007")
        sesion = Sesion.objects.create(paciente=paciente, estacion=estacion)
        self.alerta = Alerta.objects.create(
            sesion=sesion, clase_evento="posible_mareo", estado="critica", regla=regla
        )

    def test_la_tarjeta_critica_lleva_su_identificador_para_el_pitido(self):
        r = self.client.get(reverse("monitoreo:dashboard"))
        self.assertContains(r, f'data-critica="{self.alerta.pk}"')

    def test_el_dashboard_ofrece_activar_el_sonido(self):
        r = self.client.get(reverse("monitoreo:dashboard"))
        self.assertContains(r, "Activar sonido")
