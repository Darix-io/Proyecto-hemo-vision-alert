from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from pacientes.models import Estacion, Paciente, Sesion
from riesgo.models import Alerta, EventoVisual, ReglaRiesgo, Revision


class GestionHistorialTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="medico", password="clave-de-prueba-123"
        )
        self.client.force_login(self.usuario)
        regla = ReglaRiesgo.objects.create(clase_evento="hemorragia", umbral=50, ventana_segundos=60)
        self.alertas = []
        for n in (1, 2, 3):
            paciente = Paciente.objects.create(codigo=f"PAC-00{n}")
            estacion = Estacion.objects.create(codigo=f"EST-0{n}", sala="Sala A")
            sesion = Sesion.objects.create(paciente=paciente, estacion=estacion)
            self.alertas.append(Alerta.objects.create(
                sesion=sesion, clase_evento="hemorragia", estado="critica", regla=regla
            ))
        a1, a2, _ = self.alertas
        Revision.objects.create(alerta=a1, decision="confirmada", revisor=self.usuario)
        Revision.objects.create(alerta=a2, decision="descartada", revisor=self.usuario)
        EventoVisual.objects.create(
            identificador="ev-1", sesion=a1.sesion, camara="CAM-01",
            clase_evento="hemorragia", valor=95, hora_evento=timezone.now(), alerta=a1,
        )
        self.url = reverse("historial:lista")

    def test_el_resumen_clasifica_las_alertas(self):
        r = self.client.get(self.url)
        self.assertEqual(r.context["resumen"]["confirmadas"], 1)
        self.assertEqual(r.context["resumen"]["descartadas"], 1)
        self.assertEqual(r.context["resumen"]["pendientes"], 1)
        self.assertContains(r, "Confirmadas")

    def test_las_pendientes_se_listan(self):
        r = self.client.get(self.url)
        self.assertEqual(len(r.context["pendientes"]), 1)
        self.assertContains(r, "PAC-003")

    def test_eliminar_borra_la_alerta_con_su_historial(self):
        a1 = self.alertas[0]
        self.client.post(reverse("historial:eliminar", args=[a1.pk]))
        self.assertEqual(Alerta.objects.count(), 2)
        self.assertEqual(Revision.objects.count(), 1)
        self.assertEqual(EventoVisual.objects.count(), 0)

    def test_eliminar_solo_acepta_post(self):
        r = self.client.get(reverse("historial:eliminar", args=[self.alertas[0].pk]))
        self.assertEqual(r.status_code, 405)
        self.assertEqual(Alerta.objects.count(), 3)

    def test_vaciar_el_historial_revisado(self):
        self.client.post(reverse("historial:vaciar"), {"alcance": "revisadas"})
        self.assertEqual(Alerta.objects.count(), 1)
        self.assertEqual(Revision.objects.count(), 0)

    def test_vaciar_pendientes(self):
        self.client.post(reverse("historial:vaciar"), {"alcance": "pendientes"})
        self.assertEqual(Alerta.objects.count(), 2)

    def test_eliminar_todo(self):
        self.client.post(reverse("historial:vaciar"), {"alcance": "todo"})
        self.assertEqual(Alerta.objects.count(), 0)

    def test_alcance_invalido_no_borra(self):
        self.client.post(reverse("historial:vaciar"), {"alcance": "xx"})
        self.assertEqual(Alerta.objects.count(), 3)

    def test_informe_csv(self):
        r = self.client.get(reverse("historial:informe"))
        self.assertEqual(r.status_code, 200)
        self.assertIn("text/csv", r["Content-Type"])
        texto = r.content.decode("utf-8")
        self.assertIn("PAC-001", texto)
        self.assertIn("Alerta confirmada", texto)
