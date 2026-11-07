from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render

from pacientes.models import Estacion, Sesion
from riesgo.models import Alerta

from .servicios import construir_tablero


@login_required
def dashboard(request):
    contexto = construir_tablero()
    if request.GET.get("parcial"):
        return render(request, "monitoreo/_tablero.html", contexto)
    return render(request, "monitoreo/dashboard.html", contexto)


@login_required
def detalle_estacion(request, codigo):
    try:
        estacion = Estacion.objects.get(codigo=codigo)
    except Estacion.DoesNotExist:
        raise Http404("Estación no encontrada")
    sesion = (
        Sesion.objects.filter(estacion=estacion, fin__isnull=True)
        .select_related("paciente")
        .first()
    )
    alertas = []
    if sesion:
        alertas = Alerta.objects.filter(sesion=sesion).order_by("-actualizada")
    return render(
        request,
        "monitoreo/detalle_estacion.html",
        {"estacion": estacion, "sesion": sesion, "alertas": alertas},
    )