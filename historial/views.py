import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from pacientes.models import Estacion
from riesgo.models import DECISIONES_DE_CIERRE, Alerta, EventoVisual, Revision


def _revisiones(request):
    decision = request.GET.get("decision", "")
    estacion = request.GET.get("estacion", "")
    q = request.GET.get("q", "").strip()
    revisiones = Revision.objects.select_related(
        "alerta__sesion__paciente", "alerta__sesion__estacion", "revisor"
    )
    if decision in Revision.Decision.values:
        revisiones = revisiones.filter(decision=decision)
    else:
        decision = ""
    if estacion:
        revisiones = revisiones.filter(alerta__sesion__estacion__codigo=estacion)
    if q:
        revisiones = revisiones.filter(alerta__sesion__paciente__codigo__icontains=q)
    return revisiones, decision, estacion, q


def _pendientes():
    return (
        Alerta.objects.exclude(revisiones__decision__in=DECISIONES_DE_CIERRE)
        .select_related("sesion__paciente", "sesion__estacion")
        .order_by("-creada")
    )


def _resumen(pendientes):
    cuenta = {d: Revision.objects.filter(decision=d).count() for d in Revision.Decision.values}
    return {
        "alertas": Alerta.objects.count(),
        "confirmadas": cuenta["confirmada"],
        "descartadas": cuenta["descartada"],
        "observaciones": cuenta["observacion"],
        "pendientes": len(pendientes),
    }


def _borrar(alertas):
    ids = list(alertas.values_list("pk", flat=True))
    with transaction.atomic():
        Revision.objects.filter(alerta_id__in=ids).delete()
        EventoVisual.objects.filter(alerta_id__in=ids).delete()
        Alerta.objects.filter(pk__in=ids).delete()
    return len(ids)


@login_required
def historial(request):
    revisiones, decision, estacion, q = _revisiones(request)
    pendientes = list(_pendientes())
    return render(
        request,
        "historial/historial.html",
        {
            "revisiones": revisiones,
            "pendientes": pendientes,
            "resumen": _resumen(pendientes),
            "decisiones": Revision.Decision.choices,
            "estaciones": Estacion.objects.order_by("codigo"),
            "decision": decision,
            "estacion": estacion,
            "q": q,
            "consulta": request.GET.urlencode(),
        },
    )


@login_required
def informe(request):
    revisiones, *_ = _revisiones(request)
    respuesta = HttpResponse(content_type="text/csv; charset=utf-8")
    respuesta["Content-Disposition"] = 'attachment; filename="informe_historial.csv"'
    respuesta.write("\ufeff")
    escritor = csv.writer(respuesta)
    escritor.writerow(["Fecha", "Estación", "Paciente", "Evento", "Decisión", "Revisor", "Observación"])
    for r in revisiones:
        escritor.writerow([
            timezone.localtime(r.creada).strftime("%d/%m/%Y %H:%M"),
            r.alerta.sesion.estacion.codigo,
            r.alerta.sesion.paciente.codigo,
            r.alerta.get_clase_evento_display(),
            r.get_decision_display(),
            r.revisor.get_username(),
            r.observacion,
        ])
    return respuesta


@login_required
@require_POST
def eliminar(request, pk):
    alerta = get_object_or_404(Alerta, pk=pk)
    _borrar(Alerta.objects.filter(pk=alerta.pk))
    messages.success(request, "Alerta eliminada con su historial.")
    return redirect("historial:lista")


@login_required
@require_POST
def vaciar(request):
    alcance = request.POST.get("alcance", "")
    if alcance == "revisadas":
        alertas = Alerta.objects.filter(revisiones__isnull=False).distinct()
    elif alcance == "pendientes":
        alertas = Alerta.objects.exclude(revisiones__decision__in=DECISIONES_DE_CIERRE)
    elif alcance == "todo":
        alertas = Alerta.objects.all()
    else:
        messages.error(request, "Opción no válida.")
        return redirect("historial:lista")
    n = _borrar(alertas)
    messages.success(request, f"Alertas eliminadas: {n}.")
    return redirect("historial:lista")
