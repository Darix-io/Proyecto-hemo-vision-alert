from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from pacientes.models import Estacion, Sesion
from riesgo.models import DECISIONES_DE_CIERRE, Alerta, Revision

from .servicios import construir_tablero

ACCIONES = {
    "confirmar": Revision.Decision.CONFIRMADA,
    "descartar": Revision.Decision.DESCARTADA,
    "observar": Revision.Decision.OBSERVACION,
}


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
        alertas = list(Alerta.objects.filter(sesion=sesion).order_by("-actualizada"))
        cerradas = set(
            Revision.objects.filter(
                alerta__in=alertas, decision__in=DECISIONES_DE_CIERRE
            ).values_list("alerta_id", flat=True)
        )
        for alerta in alertas:
            alerta.cerrada = alerta.pk in cerradas
    return render(
        request,
        "monitoreo/detalle_estacion.html",
        {"estacion": estacion, "sesion": sesion, "alertas": alertas},
    )


@login_required
def detalle_alerta(request, pk):
    alerta = get_object_or_404(
        Alerta.objects.select_related("sesion__paciente", "sesion__estacion"), pk=pk
    )
    cerrada = alerta.revisiones.filter(decision__in=DECISIONES_DE_CIERRE).exists()
    error = ""
    observacion = ""
    if request.method == "POST":
        if cerrada:
            messages.error(request, "Esta alerta ya fue revisada.")
            return redirect("monitoreo:detalle_alerta", pk=alerta.pk)
        decision = ACCIONES.get(request.POST.get("accion"))
        observacion = request.POST.get("observacion", "").strip()
        if decision is None:
            error = "Acción no válida."
        elif decision == Revision.Decision.OBSERVACION and not observacion:
            error = "Escriba la observación para registrarla."
        else:
            revision = Revision.objects.create(
                alerta=alerta,
                decision=decision,
                observacion=observacion,
                revisor=request.user,
            )
            return redirect("monitoreo:revision_resultado", pk=revision.pk)
    return render(
        request,
        "monitoreo/detalle_alerta.html",
        {
            "alerta": alerta,
            "evento": alerta.eventos.order_by("-hora_evento").first(),
            "revisiones": alerta.revisiones.select_related("revisor"),
            "cerrada": cerrada,
            "error": error,
            "observacion": observacion,
        },
    )


@login_required
def revision_resultado(request, pk):
    revision = get_object_or_404(
        Revision.objects.select_related(
            "alerta__sesion__paciente", "alerta__sesion__estacion", "revisor"
        ),
        pk=pk,
    )
    return render(
        request,
        "monitoreo/revision_resultado.html",
        {
            "revision": revision,
            "alerta": revision.alerta,
            "cierra": revision.decision in DECISIONES_DE_CIERRE,
        },
    )