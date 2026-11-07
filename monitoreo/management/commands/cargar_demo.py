from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from pacientes.models import Estacion, Paciente, Sesion
from riesgo.models import Alerta, ReglaRiesgo

# (estación, estado de la alerta o None, ¿tiene señal reciente?)
ESCENARIO = [
    ("EST-01", "critica", True),
    ("EST-02", "critica", False),   # crítica con sin señal: nunca se oculta
    ("EST-03", "atencion", True),
    ("EST-04", "atencion", True),
    ("EST-05", "normal", True),
    ("EST-06", "normal", True),
    ("EST-07", None, True),
    ("EST-08", None, False),        # sin señal
    ("EST-21", "critica", True),
    ("EST-22", "atencion", True),
    ("EST-23", None, True),
    ("EST-24", None, False),        # sin señal
]


class Command(BaseCommand):
    help = "Carga datos de demostración para el Dashboard. Se puede repetir."

    @transaction.atomic
    def handle(self, *args, **options):
        call_command("cargar_estaciones", verbosity=0)
        regla, _ = ReglaRiesgo.objects.get_or_create(
            clase_evento="hemorragia",
            version=1,
            defaults={"umbral": 90, "ventana_segundos": 60},
        )
        ahora = timezone.now()
        for numero, (codigo, estado, con_senal) in enumerate(ESCENARIO, start=1):
            estacion = Estacion.objects.get(codigo=codigo)
            estacion.ultima_senal = ahora if con_senal else None
            estacion.save(update_fields=["ultima_senal"])
            if Sesion.objects.filter(estacion=estacion, fin__isnull=True).exists():
                continue
            paciente, _ = Paciente.objects.get_or_create(
                codigo=f"DEMO-{numero:03d}"
            )
            if Sesion.objects.filter(paciente=paciente, fin__isnull=True).exists():
                continue
            sesion = Sesion.objects.create(paciente=paciente, estacion=estacion)
            if estado:
                Alerta.objects.create(
                    sesion=sesion,
                    clase_evento="hemorragia",
                    estado=estado,
                    regla=regla,
                )
        self.stdout.write(self.style.SUCCESS("Datos de demostración listos."))