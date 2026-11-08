from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from pacientes.models import Estacion, Paciente, Sesion
from riesgo.models import Alerta, EventoVisual, ReglaRiesgo, Revision

from .servicios import construir_tablero


class RevisionTests(TestCase):
    def setUp(self):
        call_command("cargar_estaciones", verbosity=0)
        self.usuario = get_user_model().objects.create_user(
            username="medico", password="clave-de-prueba-123"
        )
        self.client.force_login(self.usuario)
        regla = ReglaRiesgo.objects.create(
            clase_evento="hemorragia", umbral=90, ventana_segundos=60
        )
        paciente = Paciente.objects.create(codigo="PAC-007")
        estacion = Estacion.objects.get(codigo="EST-07")
        estacion.ultima_senal = timezone.now()
        estacion.save()
        self.sesion = Sesion.objects.create(paciente=paciente, estacion=estacion)
        self.alerta = Alerta.objects.create(
            sesion=self.sesion, clase_evento="hemorragia", estado="critica", regla=regla
        )
        self.url = reverse("monitoreo:detalle_alerta", args=[self.alerta.pk])

    def enviar(self, accion, observacion=""):
        return self.client.post(self.url, {"accion": accion, "observacion": observacion})

    def tarjeta(self):
        for sala in construir_tablero()["salas"]:
            for t in sala["tarjetas"]:
                if t["codigo"] == "EST-07":
                    return t

    def test_el_detalle_muestra_la_alerta(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "EST-07")
        self.assertContains(r, "PAC-007")
        self.assertContains(r, "Confirmar alerta")

    def test_el_detalle_muestra_camara_del_evento(self):
        EventoVisual.objects.create(
            identificador="ev-1", sesion=self.sesion, camara="CAM-07",
            clase_evento="hemorragia", valor=94.2,
            hora_evento=timezone.now(), alerta=self.alerta,
        )
        self.assertContains(self.client.get(self.url), "CAM-07")

    def test_confirmar_cierra_la_alerta_y_sale_del_tablero(self):
        self.assertEqual(self.tarjeta()["estado"], "critica")
        r = self.enviar("confirmar")
        revision = Revision.objects.get()
        self.assertRedirects(r, reverse("monitoreo:revision_resultado", args=[revision.pk]))
        self.assertEqual(revision.decision, "confirmada")
        self.assertEqual(revision.revisor, self.usuario)
        self.assertEqual(self.tarjeta()["estado"], "normal")

    def test_descartar_cierra_la_alerta(self):
        self.enviar("descartar", "Falsa alarma")
        self.assertEqual(Revision.objects.get().decision, "descartada")
        self.assertEqual(self.tarjeta()["estado"], "normal")

    def test_observacion_sin_texto_da_error_y_no_guarda(self):
        r = self.enviar("observar", "   ")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Escriba la observación")
        self.assertEqual(Revision.objects.count(), 0)

    def test_observacion_con_texto_no_cierra_la_alerta(self):
        self.enviar("observar", "Se verificó la cámara")
        self.assertEqual(Revision.objects.count(), 1)
        self.assertEqual(self.tarjeta()["estado"], "critica")

    def test_una_alerta_cerrada_no_se_revisa_dos_veces(self):
        self.enviar("confirmar")
        r = self.enviar("descartar")
        self.assertRedirects(r, self.url)
        self.assertEqual(Revision.objects.count(), 1)

    def test_accion_invalida_no_guarda(self):
        r = self.enviar("otra")
        self.assertContains(r, "Acción no válida")
        self.assertEqual(Revision.objects.count(), 0)

    def test_la_pantalla_de_resultado_muestra_los_datos(self):
        self.enviar("confirmar", "Paciente estable")
        revision = Revision.objects.get()
        r = self.client.get(reverse("monitoreo:revision_resultado", args=[revision.pk]))
        self.assertContains(r, "EST-07")
        self.assertContains(r, "Paciente estable")
        self.assertContains(r, "Volver al Dashboard")

    def test_la_tarjeta_critica_abre_el_detalle_de_la_alerta(self):
        self.assertEqual(self.tarjeta()["alerta_id"], self.alerta.pk)
        self.assertContains(self.client.get(reverse("monitoreo:dashboard")), self.url)

    def test_exige_iniciar_sesion(self):
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code, 302)