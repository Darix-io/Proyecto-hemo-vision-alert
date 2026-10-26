from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from pacientes.models import Paciente, Sesion

from .models import Alerta, EventoVisual, ReglaRiesgo
from .services import crear_regla, regla_activa, registrar_evento

CLASE = "hemorragia"


class ReglasTests(TestCase):
    def test_rechaza_ventana_no_positiva(self):
        for ventana in (0, -5):
            with self.assertRaises(ValidationError):
                crear_regla(CLASE, 90, ventana)
        self.assertEqual(ReglaRiesgo.objects.count(), 0)

    def test_rechaza_clase_inexistente(self):
        with self.assertRaises(ValidationError):
            crear_regla("otra", 90, 60)
        self.assertEqual(ReglaRiesgo.objects.count(), 0)

    def test_crea_una_regla_valida(self):
        regla = crear_regla(CLASE, 90, 60)
        self.assertEqual(regla.version, 1)
        self.assertTrue(regla.activa)
        self.assertEqual(regla_activa(CLASE), regla)

    def test_una_regla_nueva_es_una_version_nueva(self):
        v1 = crear_regla(CLASE, 90, 60)
        v2 = crear_regla(CLASE, 85, 60)
        v1.refresh_from_db()
        self.assertEqual(v2.version, 2)
        self.assertFalse(v1.activa)
        self.assertEqual(regla_activa(CLASE), v2)
        self.assertEqual(ReglaRiesgo.objects.count(), 2)

    def test_una_regla_invalida_no_cambia_las_existentes(self):
        v1 = crear_regla(CLASE, 90, 60)
        with self.assertRaises(ValidationError):
            crear_regla(CLASE, 85, 0)
        v1.refresh_from_db()
        self.assertTrue(v1.activa)
        self.assertEqual(ReglaRiesgo.objects.count(), 1)


class EventosTests(TestCase):
    def setUp(self):
        paciente = Paciente.objects.create(codigo="PAC-001")
        self.sesion = Sesion.objects.create(paciente=paciente, estacion="EST-07")
        self.regla = crear_regla(CLASE, 90, 60)
        self.t0 = timezone.now()

    def registrar(self, identificador, valor, segundos=0, sesion=None, **extra):
        return registrar_evento(
            identificador,
            sesion or self.sesion,
            CLASE,
            self.t0 + timedelta(seconds=segundos),
            valor=valor,
            **extra,
        )

    def test_bajo_igual_y_sobre_el_umbral(self):
        esperado = [("E-1", 89.99, "normal"), ("E-2", 90, "critica"), ("E-3", 95, "critica")]
        for i, (identificador, valor, estado) in enumerate(esperado):
            _, alerta, _ = self.registrar(identificador, valor, segundos=i * 600)
            self.assertEqual(alerta.estado, estado)
        self.assertEqual(Alerta.objects.count(), 3)

    def test_repetir_el_mismo_evento_no_crea_otra_alerta(self):
        _, alerta1, creado1 = self.registrar("E-1", 95)
        _, alerta2, creado2 = self.registrar("E-1", 95)
        _, alerta3, creado3 = self.registrar("E-1", 95)
        self.assertEqual([creado1, creado2, creado3], [True, False, False])
        self.assertEqual(alerta1, alerta2)
        self.assertEqual(alerta1, alerta3)
        self.assertEqual(EventoVisual.objects.count(), 1)
        self.assertEqual(Alerta.objects.count(), 1)

    def test_eventos_dentro_de_la_ventana_comparten_alerta(self):
        _, alerta1, _ = self.registrar("E-1", 95)
        _, alerta2, _ = self.registrar("E-2", 96, segundos=30)
        self.assertEqual(alerta1, alerta2)
        self.assertEqual(Alerta.objects.count(), 1)
        self.assertEqual(alerta1.eventos.count(), 2)

    def test_eventos_fuera_de_la_ventana_crean_otra_alerta(self):
        _, alerta1, _ = self.registrar("E-1", 95)
        _, alerta2, _ = self.registrar("E-2", 96, segundos=120)
        self.assertNotEqual(alerta1, alerta2)
        self.assertEqual(Alerta.objects.count(), 2)

    def test_eventos_de_otra_sesion_no_se_agrupan(self):
        otro = Paciente.objects.create(codigo="PAC-002")
        otra_sesion = Sesion.objects.create(paciente=otro, estacion="EST-08")
        _, alerta1, _ = self.registrar("E-1", 95)
        _, alerta2, _ = self.registrar("E-2", 95, sesion=otra_sesion)
        self.assertNotEqual(alerta1, alerta2)

    def test_la_alerta_sube_a_critica_y_no_baja(self):
        _, alerta, _ = self.registrar("E-1", 50)
        self.assertEqual(alerta.estado, "normal")
        self.registrar("E-2", 95, segundos=10)
        alerta.refresh_from_db()
        self.assertEqual(alerta.estado, "critica")
        self.registrar("E-3", 10, segundos=20)
        alerta.refresh_from_db()
        self.assertEqual(alerta.estado, "critica")
        self.assertEqual(Alerta.objects.count(), 1)

    def test_evento_sin_valor_no_inventa_nada(self):
        _, alerta, creado = self.registrar("E-1", None)
        self.assertTrue(creado)
        self.assertIsNone(alerta)
        self.assertIsNone(EventoVisual.objects.get(identificador="E-1").valor)
        self.assertEqual(Alerta.objects.count(), 0)

    def test_evento_sin_regla_se_guarda_sin_alerta(self):
        ReglaRiesgo.objects.all().delete()
        _, alerta, creado = self.registrar("E-1", 95)
        self.assertTrue(creado)
        self.assertIsNone(alerta)
        self.assertEqual(EventoVisual.objects.count(), 1)

    def test_la_alerta_conserva_campos_y_orden_temporal(self):
        self.registrar("E-1", 92, segundos=0, camara="CAM-07")
        self.registrar("E-2", 95, segundos=10)
        self.registrar("E-3", 91, segundos=20)
        alerta = Alerta.objects.get()
        orden = list(
            alerta.eventos.order_by("hora_evento").values_list("identificador", flat=True)
        )
        self.assertEqual(orden, ["E-1", "E-2", "E-3"])
        primero = EventoVisual.objects.get(identificador="E-1")
        self.assertEqual(primero.camara, "CAM-07")
        self.assertEqual(primero.valor, Decimal("92.00"))
        self.assertEqual(primero.hora_evento, self.t0)
        self.assertEqual(primero.clase_evento, CLASE)
        self.assertEqual(alerta.sesion, self.sesion)
        self.assertEqual(alerta.estado, "critica")
        self.assertEqual(alerta.regla.version, 1)

    def test_rechaza_clase_inexistente_y_valor_fuera_de_rango(self):
        with self.assertRaises(ValidationError):
            registrar_evento("E-1", self.sesion, "otra", self.t0, valor=95)
        with self.assertRaises(ValidationError):
            self.registrar("E-2", 150)
        self.assertEqual(EventoVisual.objects.count(), 0)

    def test_la_alerta_conserva_la_version_de_su_regla(self):
        _, alerta, _ = self.registrar("E-1", 95)
        crear_regla(CLASE, 80, 60)
        alerta.refresh_from_db()
        self.assertEqual(alerta.regla.version, 1)
        _, nueva, _ = self.registrar("E-2", 85, segundos=600)
        self.assertEqual(nueva.regla.version, 2)