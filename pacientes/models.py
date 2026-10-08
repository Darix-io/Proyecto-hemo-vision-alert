from django.db import models

# Create your models here.

class Paciente(models.Model):
    codigo = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.codigo

    
class Sesion(models.Model):
    paciente = models.ForeignKey(
        Paciente, on_delete=models.PROTECT, related_name="sesiones"
    )
    estacion = models.CharField(max_length=30)
    inicio = models.DateTimeField(auto_now_add=True)
    fin = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["estacion"],
                condition=models.Q(fin__isnull=True),
                name="una_sesion_activa_por_estacion",
            )
        ]

    def __str__(self):
        return f"{self.paciente} - {self.estacion}"