from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from pacientes.models import Estacion, Paciente, Sesion
from riesgo.models import Alerta, ReglaRiesgo

from .servicios import construir_tablero


def tarjeta(tablero, codigo):
    for sala in tablero["salas"]:
        for t in sala["tarjetas"]:
            if t["codigo"] == codigo:
                return t


class TableroTests(TestCase):
    def setUp(self):
        call_command("cargar_estaciones", verbosity=0)
        self.ahora = timezone.now()
        self.regla = ReglaRiesgo.objects.create(
            clase_evento="hemorragia", umbral=90, ventana_segundos=60
        )
        self.n = 0

    def sesion(self, codigo, segundos_desde_senal=None):
        self.n += 1
        paciente = Paciente.objects.create(codigo=f"PAC-{self.n:03d}")
        estacion = Estacion.objects.get(codigo=codigo)
        if segundos_desde_senal is not None:
            estacion.ultima_senal = self.ahora - timedelta(seconds=segundos_desde_senal)
            estacion.save()
        return Sesion.objects.create(paciente=paciente, estacion=estacion)

    def alerta(self, sesion, estado):
        return Alerta.objects.create(
            sesion=sesion, clase_evento="hemorragia", estado=estado, regla=self.regla
        )

    def test_al_inicio_las_40_estan_libres(self):
        tablero = construir_tablero(self.ahora)
        self.assertEqual(tablero["contadores"]["libres"], 40)
        self.assertEqual(tablero["contadores"]["total"], 40)
        self.assertEqual([s["nombre"] for s in tablero["salas"]], ["Sala A", "Sala B"])

    def test_con_senal_reciente_es_normal(self):
        self.sesion("EST-01", 3)
        t = tarjeta(construir_tablero(self.ahora), "EST-01")
        self.assertEqual(t["estado"], "normal")
        self.assertEqual(t["paciente"], "PAC-001")

    def test_sin_senal_a_los_10_segundos(self):
        self.sesion("EST-02", 11)
        t = tarjeta(construir_tablero(self.ahora), "EST-02")
        self.assertEqual(t["estado"], "sin_senal")

    def test_sesion_que_nunca_tuvo_senal_es_sin_senal(self):
        self.sesion("EST-02")
        t = tarjeta(construir_tablero(self.ahora), "EST-02")
        self.assertEqual(t["estado"], "sin_senal")

    def test_estacion_libre_no_se_evalua_como_sin_senal(self):
        t = tarjeta(construir_tablero(self.ahora), "EST-03")
        self.assertEqual(t["estado"], "libre")
        self.assertFalse(t["sin_senal"])
        self.assertIsNone(t["paciente"])

    def test_critica_sin_senal_se_muestra_critica_y_cuenta_una_vez(self):
        sesion = self.sesion("EST-04", 30)
        self.alerta(sesion, "critica")
        tablero = construir_tablero(self.ahora)
        t = tarjeta(tablero, "EST-04")
        self.assertEqual(t["estado"], "critica")
        self.assertTrue(t["sin_senal"])
        self.assertEqual(tablero["contadores"]["criticas"], 1)
        self.assertEqual(tablero["contadores"]["sin_senal"], 0)

    def test_la_alerta_mas_grave_manda(self):
        sesion = self.sesion("EST-05", 2)
        self.alerta(sesion, "normal")
        self.alerta(sesion, "critica")
        t = tarjeta(construir_tablero(self.ahora), "EST-05")
        self.assertEqual(t["estado"], "critica")

    def test_atencion(self):
        sesion = self.sesion("EST-06", 2)
        self.alerta(sesion, "atencion")
        t = tarjeta(construir_tablero(self.ahora), "EST-06")
        self.assertEqual(t["estado"], "atencion")

    def test_una_alerta_normal_no_es_urgente(self):
        sesion = self.sesion("EST-07", 2)
        self.alerta(sesion, "normal")
        t = tarjeta(construir_tablero(self.ahora), "EST-07")
        self.assertEqual(t["estado"], "normal")

    def test_orden_por_gravedad_y_libres_al_final(self):
        self.alerta(self.sesion("EST-10", 2), "critica")
        self.sesion("EST-11", 2)
        sala_a = construir_tablero(self.ahora)["salas"][0]["tarjetas"]
        estados = [t["estado"] for t in sala_a]
        self.assertEqual(estados[0], "critica")
        self.assertEqual(estados[1], "normal")
        self.assertEqual(estados[-1], "libre")

    def test_estaciones_inactivas_no_aparecen(self):
        Estacion.objects.filter(codigo="EST-20").update(activa=False)
        tablero = construir_tablero(self.ahora)
        self.assertEqual(tablero["contadores"]["total"], 39)
        self.assertIsNone(tarjeta(tablero, "EST-20"))


class DashboardVistaTests(TestCase):
    def setUp(self):
        call_command("cargar_estaciones", verbosity=0)

    def test_exige_iniciar_sesion(self):
        respuesta = self.client.get(reverse("monitoreo:dashboard"))
        destino = f"{reverse('seguridad:login')}?next={reverse('monitoreo:dashboard')}"
        self.assertRedirects(respuesta, destino)

    def test_muestra_las_dos_salas_y_el_contador_de_libres(self):
        usuario = get_user_model().objects.create_user(
            username="enfermeria", password="clave-de-prueba-123"
        )
        self.client.force_login(usuario)
        respuesta = self.client.get(reverse("monitoreo:dashboard"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Sala A")
        self.assertContains(respuesta, "Sala B")
        self.assertContains(respuesta, "Libres")

    def test_la_version_parcial_no_incluye_la_pagina_completa(self):
        usuario = get_user_model().objects.create_user(
            username="enfermeria", password="clave-de-prueba-123"
        )
        self.client.force_login(usuario)
        respuesta = self.client.get(reverse("monitoreo:dashboard") + "?parcial=1")
        self.assertEqual(respuesta.status_code, 200)
        self.assertNotContains(respuesta, "<html")
        self.assertContains(respuesta, "Sala A")

class CargarDemoTests(TestCase):
    def test_carga_el_escenario_y_se_puede_repetir(self):
        call_command("cargar_demo", verbosity=0)
        call_command("cargar_demo", verbosity=0)
        self.assertEqual(Sesion.objects.filter(fin__isnull=True).count(), 12)
        tablero = construir_tablero()
        self.assertEqual(tablero["contadores"]["criticas"], 3)
        self.assertEqual(tablero["contadores"]["libres"], 28)

    def test_critica_sin_senal_sigue_critica(self):
        call_command("cargar_demo", verbosity=0)
        t = tarjeta(construir_tablero(), "EST-02")
        self.assertEqual(t["estado"], "critica")
        self.assertTrue(t["sin_senal"])