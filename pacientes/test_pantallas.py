from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Estacion, Paciente, Sesion


class PantallasTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="enfermeria", password="clave-de-prueba-123"
        )
        estacion = Estacion.objects.create(
            codigo="EST-01", sala="Sala A", ultima_senal=timezone.now()
        )
        p1 = Paciente.objects.create(codigo="PAC-001")
        Paciente.objects.create(codigo="PAC-002")
        Sesion.objects.create(paciente=p1, estacion=estacion)

    def test_lista_muestra_estacion_y_estado(self):
        self.client.force_login(self.usuario)
        r = self.client.get(reverse("pacientes:lista"))
        self.assertContains(r, "EST-01")
        self.assertContains(r, "Normal")
        self.assertContains(r, "Sin sesión")

    def test_buscador_filtra_por_codigo(self):
        self.client.force_login(self.usuario)
        r = self.client.get(reverse("pacientes:lista") + "?q=PAC-002")
        self.assertContains(r, "PAC-002")
        self.assertNotContains(r, "PAC-001")

    def test_buscador_sin_resultados(self):
        self.client.force_login(self.usuario)
        r = self.client.get(reverse("pacientes:lista") + "?q=ZZZ")
        self.assertContains(r, "Sin resultados")

    def test_login_muestra_el_panel(self):
        r = self.client.get(reverse("seguridad:login"))
        self.assertContains(r, "Monitoreo inteligente para hemodiálisis")

    def test_login_incorrecto_muestra_el_error(self):
        r = self.client.post(
            reverse("seguridad:login"), {"username": "enfermeria", "password": "mala"}
        )
        self.assertContains(r, "Credenciales incorrectas.")