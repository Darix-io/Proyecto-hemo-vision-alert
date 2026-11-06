from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .servicios import construir_tablero


@login_required
def dashboard(request):
    contexto = construir_tablero()
    if request.GET.get("parcial"):
        return render(request, "monitoreo/_tablero.html", contexto)
    return render(request, "monitoreo/dashboard.html", contexto)
