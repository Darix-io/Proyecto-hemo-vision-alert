from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max

from .models import Alerta, ClaseEvento, EventoVisual, ReglaRiesgo

def clasificar_valor(valor, regla):
    """Devuelve el estado que corresponde a un valor según la regla.

    Si no hay valor, no se clasifica ni se inventa uno: devuelve None.
    """
    if valor is None:
        return None
    if valor >= regla.umbral:
        return Alerta.Estado.CRITICA
    return Alerta.Estado.NORMAL


def regla_activa(clase_evento):
    """Devuelve la regla vigente de una clase de evento, o None."""
    return (
        ReglaRiesgo.objects.filter(clase_evento=clase_evento, activa=True)
        .order_by("-version")
        .first()
    )


@transaction.atomic
def crear_regla(clase_evento, umbral, ventana_segundos):
    """Crea una versión nueva de la regla y desactiva la anterior.

    Lanza ValidationError si la ventana no es positiva o la clase no existe;
    en ese caso no se cambia nada.
    """
    ultima = (
        ReglaRiesgo.objects.filter(clase_evento=clase_evento).aggregate(
            m=Max("version")
        )["m"]
        or 0
    )
    regla = ReglaRiesgo(
        clase_evento=clase_evento,
        umbral=umbral,
        ventana_segundos=ventana_segundos,
        version=ultima + 1,
    )
    regla.full_clean()
    ReglaRiesgo.objects.filter(clase_evento=clase_evento, activa=True).update(
        activa=False
    )
    regla.save()
    return regla

@transaction.atomic
def registrar_evento(
    identificador, sesion, clase_evento, hora_evento, valor=None, camara=""
):
    """Registra un evento, lo clasifica y lo agrupa en una alerta.

    Devuelve (evento, alerta, creado). Repetir un identificador no crea
    otro evento ni otra alerta.
    """
    if clase_evento not in ClaseEvento.values:
        raise ValidationError(f"Clase de evento inexistente: {clase_evento}")
    if valor is not None and not 0 <= valor <= 100:
        raise ValidationError("El valor debe estar entre 0 y 100.")

    evento, creado = EventoVisual.objects.get_or_create(
        identificador=identificador,
        defaults={
            "sesion": sesion,
            "clase_evento": clase_evento,
            "hora_evento": hora_evento,
            "valor": valor,
            "camara": camara,
        },
    )
    if not creado:
        return evento, evento.alerta, False

    regla = regla_activa(clase_evento)
    estado = clasificar_valor(valor, regla) if regla else None
    if estado is None:
        return evento, None, True

    ventana = timedelta(seconds=regla.ventana_segundos)
    vecino = (
        EventoVisual.objects.filter(
            sesion=sesion,
            clase_evento=clase_evento,
            alerta__isnull=False,
            hora_evento__gte=hora_evento - ventana,
            hora_evento__lte=hora_evento + ventana,
        )
        .exclude(pk=evento.pk)
        .select_related("alerta")
        .order_by("-hora_evento")
        .first()
    )
    if vecino:
        alerta = vecino.alerta
        if estado == Alerta.Estado.CRITICA and alerta.estado != Alerta.Estado.CRITICA:
            alerta.estado = estado
            alerta.regla = regla
            alerta.save(update_fields=["estado", "regla", "actualizada"])
    else:
        alerta = Alerta.objects.create(
            sesion=sesion, clase_evento=clase_evento, estado=estado, regla=regla
        )

    evento.alerta = alerta
    evento.save(update_fields=["alerta"])
    return evento, alerta, True