from django.core.management.base import BaseCommand

from riesgo.models import ClaseEvento
from riesgo.services import crear_regla, regla_activa

UMBRAL = 50
VENTANA_SEGUNDOS = 60


class Command(BaseCommand):
    help = "Crea una regla activa por cada clase de evento que no la tenga. Se puede repetir."

    def handle(self, *args, **options):
        creadas = 0
        for clase in ClaseEvento.values:
            if regla_activa(clase) is None:
                crear_regla(clase, UMBRAL, VENTANA_SEGUNDOS)
                creadas += 1
        self.stdout.write(
            self.style.SUCCESS(
                f"Reglas listas: {creadas} creadas, {len(ClaseEvento.values) - creadas} ya existían."
            )
        )
