import json
from datetime import datetime
from decimal import Decimal, InvalidOperation
from functools import wraps
import hmac

from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from pacientes.models import Estacion, Sesion

from .services import registrar_evento


def con_token(vista):
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        esperado = getattr(settings, "VISION_TOKEN", "")
        recibido = request.headers.get("X-Vision-Token", "")
        if not esperado or not hmac.compare_digest(esperado, recibido):
            return JsonResponse({"error": "Token no válido."}, status=401)
        return vista(request, *args, **kwargs)

    return envoltura


def leer_json(request):
    try:
        datos = json.loads(request.body or b"{}")
    except ValueError:
        return None
    return datos if isinstance(datos, dict) else None


@csrf_exempt
@require_POST
@con_token
def senal(request):
    datos = leer_json(request)
    if datos is None or not datos.get("estacion"):
        return JsonResponse({"error": "Falta la estación."}, status=400)
    actualizadas = Estacion.objects.filter(
        codigo=datos["estacion"], activa=True
    ).update(ultima_senal=timezone.now())
    if not actualizadas:
        return JsonResponse({"error": "Estación no encontrada."}, status=404)
    return JsonResponse({"ok": True})


@csrf_exempt
@require_POST
@con_token
def evento(request):
    datos = leer_json(request)
    if datos is None:
        return JsonResponse({"error": "JSON no válido."}, status=400)
    identificador = str(datos.get("identificador", "")).strip()
    codigo = str(datos.get("estacion", "")).strip()
    clase = datos.get("clase_evento", "")
    if not identificador or not codigo or not clase:
        return JsonResponse({"error": "Faltan campos obligatorios."}, status=400)
    try:
        valor = None if datos.get("valor") is None else Decimal(str(datos["valor"]))
    except InvalidOperation:
        return JsonResponse({"error": "Valor no válido."}, status=400)
    hora = parse_datetime(str(datos.get("hora_evento", ""))) or timezone.now()
    if timezone.is_naive(hora):
        hora = timezone.make_aware(hora)

    sesion = (
        Sesion.objects.filter(estacion__codigo=codigo, fin__isnull=True)
        .select_related("estacion")
        .first()
    )
    if sesion is None:
        return JsonResponse({"error": "La estación no tiene sesión activa."}, status=409)
    try:
        ev, alerta, creado = registrar_evento(
            identificador, sesion, clase, hora,
            valor=valor, camara=str(datos.get("camara", "")),
        )
    except ValidationError as error:
        return JsonResponse({"error": " ".join(error.messages)}, status=400)
    return JsonResponse(
        {
            "ok": True,
            "creado": creado,
            "alerta": alerta.pk if alerta else None,
            "estado": alerta.estado if alerta else None,
        },
        status=201 if creado else 200,
    )