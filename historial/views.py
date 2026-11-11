from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from pacientes.models import Estacion
from riesgo.models import Revision


@login_required
def historial(request):
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

    return render(
        request,
        "historial/historial.html",
        {
            "revisiones": revisiones,
            "decisiones": Revision.Decision.choices,
            "estaciones": Estacion.objects.order_by("codigo"),
            "decision": decision,
            "estacion": estacion,
            "q": q,
        },
    )