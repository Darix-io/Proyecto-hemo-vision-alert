from datetime import timedelta

from django.utils import timezone

from pacientes.models import Estacion, Sesion
from riesgo.models import DECISIONES_DE_CIERRE, Alerta

SEGUNDOS_SIN_SENAL = 10

ETIQUETAS = {
    "critica": "Crítica",
    "sin_senal": "Sin señal",
    "atencion": "En atención",
    "normal": "Normal",
    "libre": "Libre",
}
SIMBOLOS = {
    "critica": "▲",
    "sin_senal": "○",
    "atencion": "●",
    "normal": "✓",
    "libre": "–",
}
ORDEN = {"critica": 0, "sin_senal": 1, "atencion": 2, "normal": 3, "libre": 4}


def estado_de_alertas(estados):
    """Toma el estado más grave de las alertas pendientes de la sesión."""
    if Alerta.Estado.CRITICA in estados:
        return "critica"
    if Alerta.Estado.ATENCION in estados:
        return "atencion"
    return "normal"


def construir_tablero(ahora=None):
    ahora = ahora or timezone.now()
    limite = ahora - timedelta(seconds=SEGUNDOS_SIN_SENAL)

    estaciones = list(Estacion.objects.filter(activa=True))
    sesiones = {
        s.estacion_id: s
        for s in Sesion.objects.filter(
            fin__isnull=True, estacion__in=estaciones
        ).select_related("paciente")
    }

    # Solo cuentan las alertas pendientes: las confirmadas o descartadas ya se cerraron.
    pares = (
        Alerta.objects.filter(sesion_id__in=[s.pk for s in sesiones.values()])
        .exclude(revisiones__decision__in=DECISIONES_DE_CIERRE)
        .values_list("sesion_id", "estado", "pk")
    )
    estados_por_sesion = {}
    critica_por_sesion = {}
    for sesion_id, estado, pk in pares:
        estados_por_sesion.setdefault(sesion_id, set()).add(estado)
        if estado == Alerta.Estado.CRITICA:
            critica_por_sesion[sesion_id] = max(pk, critica_por_sesion.get(sesion_id, 0))

    por_sala = {}
    for estacion in estaciones:
        sesion = sesiones.get(estacion.pk)
        alerta_id = None
        if sesion is None:
            estado, sin_senal, paciente = "libre", False, None
        else:
            paciente = sesion.paciente.codigo
            sin_senal = (
                estacion.ultima_senal is None or estacion.ultima_senal <= limite
            )
            estado = estado_de_alertas(estados_por_sesion.get(sesion.pk, set()))
            alerta_id = critica_por_sesion.get(sesion.pk)
            if sin_senal and estado != "critica":
                estado = "sin_senal"
        sala = estacion.sala or "Sin sala"
        por_sala.setdefault(sala, []).append(
            {
                "codigo": estacion.codigo,
                "estacion_id": estacion.pk,
                "sala": sala,
                "estado": estado,
                "etiqueta": ETIQUETAS[estado],
                "simbolo": SIMBOLOS[estado],
                "sin_senal": sin_senal,
                "paciente": paciente,
                "ultima_senal": estacion.ultima_senal,
                "alerta_id": alerta_id,
            }
        )

    salas = []
    contadores = {
        "criticas": 0, "sin_senal": 0, "atenciones": 0,
        "normales": 0, "libres": 0, "total": 0, "activas": 0,
    }
    clave = {
        "critica": "criticas", "sin_senal": "sin_senal", "atencion": "atenciones",
        "normal": "normales", "libre": "libres",
    }
    for nombre in sorted(por_sala):
        tarjetas = sorted(
            por_sala[nombre], key=lambda t: (ORDEN[t["estado"]], t["codigo"])
        )
        for t in tarjetas:
            contadores[clave[t["estado"]]] += 1
            contadores["total"] += 1
            if t["estado"] != "libre":
                contadores["activas"] += 1
        salas.append({"nombre": nombre, "tarjetas": tarjetas})

    return {
        "salas": salas,
        "contadores": contadores,
        "actualizado": ahora,
        "nombres_salas": sorted(por_sala),
    }