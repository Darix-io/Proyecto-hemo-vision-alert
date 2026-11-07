import time

from django.core.management.base import BaseCommand
from django.utils import timezone

from pacientes.models import Estacion, Sesion


class Command(BaseCommand):
    help = "Renueva la señal de las estaciones con sesión activa, salvo las que se dejan sin señal. Ctrl + C para detener."

    SIN_SENAL = {"EST-02", "EST-08", "EST-24"}

    def add_arguments(self, parser):
        parser.add_argument("--cada", type=int, default=3, help="Segundos entre renovaciones.")

    def handle(self, *args, **options):
        self.stdout.write("Simulando señal. Ctrl + C para detener.")
        try:
            while True:
                codigos = (
                    Sesion.objects.filter(fin__isnull=True)
                    .values_list("estacion__codigo", flat=True)
                )
                Estacion.objects.filter(
                    codigo__in=[c for c in codigos if c not in self.SIN_SENAL]
                ).update(ultima_senal=timezone.now())
                time.sleep(options["cada"])
        except KeyboardInterrupt:
            self.stdout.write("Simulación detenida.")