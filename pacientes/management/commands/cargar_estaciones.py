from django.core.management.base import BaseCommand

from pacientes.models import Estacion


class Command(BaseCommand):
    help = "Carga las 40 estaciones simuladas (Sala A y Sala B). Se puede repetir."

    def handle(self, *args, **options):
        creadas = 0
        for numero in range(1, 41):
            codigo = f"EST-{numero:02d}"
            sala = "Sala A" if numero <= 20 else "Sala B"
            _, nueva = Estacion.objects.update_or_create(
                codigo=codigo, defaults={"sala": sala, "activa": True}
            )
            creadas += nueva
        self.stdout.write(
            self.style.SUCCESS(
                f"Estaciones listas: {creadas} creadas, {40 - creadas} ya existían."
            )
        )