from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class ClaseEvento(models.TextChoices):
    HEMORRAGIA = "hemorragia", "Posible hemorragia"


class ReglaRiesgo(models.Model):
    clase_evento = models.CharField(max_length=40, choices=ClaseEvento.choices)
    umbral = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    ventana_segundos = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    version = models.PositiveIntegerField(default=1)
    activa = models.BooleanField(default=True)
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["clase_evento", "version"],
                name="regla_unica_por_clase_y_version",
            ),
            models.CheckConstraint(
                condition=models.Q(ventana_segundos__gt=0),
                name="ventana_positiva",
            ),
        ]

    def __str__(self):
        return f"{self.clase_evento} v{self.version}"


class Alerta(models.Model):
    class Estado(models.TextChoices):
        NORMAL = "normal", "Normal"
        ATENCION = "atencion", "En atención"
        CRITICA = "critica", "Crítica"

    sesion = models.ForeignKey(
        "pacientes.Sesion", on_delete=models.PROTECT, related_name="alertas"
    )
    clase_evento = models.CharField(max_length=40, choices=ClaseEvento.choices)
    estado = models.CharField(max_length=10, choices=Estado.choices)
    regla = models.ForeignKey(
        ReglaRiesgo, on_delete=models.PROTECT, related_name="alertas"
    )
    creada = models.DateTimeField(auto_now_add=True)
    actualizada = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.clase_evento} {self.estado} (sesión {self.sesion_id})"


class EventoVisual(models.Model):
    identificador = models.CharField(max_length=64, unique=True)
    sesion = models.ForeignKey(
        "pacientes.Sesion", on_delete=models.PROTECT, related_name="eventos"
    )
    camara = models.CharField(max_length=30, blank=True)
    clase_evento = models.CharField(max_length=40, choices=ClaseEvento.choices)
    valor = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    hora_evento = models.DateTimeField()
    alerta = models.ForeignKey(
        Alerta,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="eventos",
    )

    def __str__(self):
        return self.identificador
