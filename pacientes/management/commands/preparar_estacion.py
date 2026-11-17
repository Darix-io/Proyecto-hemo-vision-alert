from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from pacientes.models import Estacion, Paciente, Sesion


class Command(BaseCommand):
    help = "Prepara una estación para la prueba: la activa, carga las reglas y abre una sesión. Se puede repetir."

    def add_arguments(self, parser):
        parser.add_argument("codigo", help="Ejemplo: EST-12")

    def handle(self, *args, **options):
        codigo = options["codigo"].strip().upper()
        try:
            estacion = Estacion.objects.get(codigo=codigo)
        except Estacion.DoesNotExist:
            raise CommandError(f"La estación {codigo} no existe. Ejecute cargar_estaciones.")
        if not estacion.activa:
            estacion.activa = True
            estacion.save(update_fields=["activa"])
        call_command("cargar_reglas", verbosity=0)
        if Sesion.objects.filter(estacion=estacion, fin__isnull=True).exists():
            self.stdout.write(self.style.SUCCESS(f"{codigo} ya tenía una sesión activa."))
            return
        paciente, _ = Paciente.objects.get_or_create(codigo=f"PAC-{codigo.split('-')[-1]}")
        if Sesion.objects.filter(paciente=paciente, fin__isnull=True).exists():
            raise CommandError(f"{paciente.codigo} ya tiene una sesión activa en otra estación.")
        Sesion.objects.create(paciente=paciente, estacion=estacion)
        self.stdout.write(self.style.SUCCESS(f"{codigo} lista con el paciente {paciente.codigo}."))
