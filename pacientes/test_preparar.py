from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from riesgo.models import ClaseEvento, ReglaRiesgo

from .models import Estacion, Paciente, Sesion


class PrepararEstacionTests(TestCase):
    def setUp(self):
        call_command("cargar_estaciones", verbosity=0)

    def test_abre_sesion_y_carga_las_reglas(self):
        call_command("preparar_estacion", "EST-12", verbosity=0)
        self.assertEqual(Sesion.objects.get().estacion.codigo, "EST-12")
        self.assertTrue(Paciente.objects.filter(codigo="PAC-12").exists())
        self.assertEqual(ReglaRiesgo.objects.filter(activa=True).count(), len(ClaseEvento.values))

    def test_se_puede_repetir_sin_duplicar(self):
        call_command("preparar_estacion", "est-12", verbosity=0)
        call_command("preparar_estacion", "EST-12", verbosity=0)
        self.assertEqual(Sesion.objects.count(), 1)

    def test_estacion_inexistente_da_error(self):
        with self.assertRaises(CommandError):
            call_command("preparar_estacion", "EST-99", verbosity=0)
