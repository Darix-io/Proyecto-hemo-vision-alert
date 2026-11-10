from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from pacientes.models import Estacion, Paciente, Sesion
from riesgo.models import Alerta, ReglaRiesgo, Revision


class HistorialTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="medico", password="clave-de-prueba-123"
        )
        self.client.force_login(self.usuario)
        regla = ReglaRiesgo.objects.create(
            clase_evento="hemorragia", umbral=90, ventana_segundos=60
        )
        for n, decision in ((1, "confirmada"), (2, "descartada")):
            paciente = Paciente.objects.create(codigo=f"PAC-00{n}")
            estacion = Estacion.objects.create(codigo=f"EST-0{n}", sala="Sala A")
            sesion = Sesion.objects.create(paciente=paciente, estacion=estacion)
            alerta = Alerta.objects.create(
                sesion=sesion, clase_evento="hemorragia", estado="critica", regla=regla
            )
            Revision.objects.create(
                alerta=alerta, decision=decision, observacion=f"obs {n}", revisor=self.usuario
            )
        self.url = reverse("historial:lista")

    def test_lista_todas_las_revisiones(self):
        r = self.client.get(self.url)
        self.assertContains(r, "PAC-001")
        self.assertContains(r, "PAC-002")

    def test_filtra_por_decision(self):
        r = self.client.get(self.url + "?decision=descartada")
        self.assertContains(r, "PAC-002")
        self.assertNotContains(r, "PAC-001")

    def test_filtra_por_estacion(self):
        r = self.client.get(self.url + "?estacion=EST-01")
        self.assertContains(r, "PAC-001")
        self.assertNotContains(r, "PAC-002")

    def test_busca_por_paciente(self):
        r = self.client.get(self.url + "?q=PAC-002")
        self.assertContains(r, "PAC-002")
        self.assertNotContains(r, "PAC-001")

    def test_decision_invalida_se_ignora(self):
        r = self.client.get(self.url + "?decision=xxx")
        self.assertContains(r, "PAC-001")

    def test_sin_revisiones(self):
        Revision.objects.all().delete()
        self.assertContains(self.client.get(self.url), "Todavía no hay revisiones")

    def test_exige_iniciar_sesion(self):
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code, 302)