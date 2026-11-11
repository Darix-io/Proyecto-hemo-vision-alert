from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from pacientes.models import Estacion, Paciente, Sesion

from .models import ClaseEvento, ReglaRiesgo
from .services import crear_regla, regla_activa, registrar_evento


class ClasesDePoseTests(TestCase):
    def setUp(self):
        estacion = Estacion.objects.create(codigo="EST-07", sala="Sala A")
        paciente = Paciente.objects.create(codigo="PAC-007")
        self.sesion = Sesion.objects.create(paciente=paciente, estacion=estacion)

    def cargar(self):
        call_command("cargar_reglas", verbosity=0)

    def test_cargar_reglas_crea_una_regla_activa_por_clase(self):
        self.cargar()
        for clase in ClaseEvento.values:
            self.assertEqual(
                ReglaRiesgo.objects.filter(clase_evento=clase, activa=True).count(), 1
            )

    def test_cargar_reglas_se_puede_repetir(self):
        self.cargar()
        self.cargar()
        self.assertEqual(ReglaRiesgo.objects.count(), len(ClaseEvento.values))

    def test_respeta_una_regla_existente(self):
        crear_regla("hemorragia", 90, 60)
        self.cargar()
        self.assertEqual(ReglaRiesgo.objects.filter(clase_evento="hemorragia").count(), 1)
        self.assertEqual(regla_activa("hemorragia").umbral, 90)

    def critica(self, clase):
        self.cargar()
        _, alerta, _ = registrar_evento(
            f"ev-{clase}", self.sesion, clase, timezone.now(),
            valor=Decimal("87.50"), camara="CAM-07",
        )
        self.assertEqual(alerta.estado, "critica")
        self.assertEqual(alerta.clase_evento, clase)

    def test_posible_mareo_es_critico(self):
        self.critica("posible_mareo")

    def test_movimiento_brusco_es_critico(self):
        self.critica("movimiento_brusco")