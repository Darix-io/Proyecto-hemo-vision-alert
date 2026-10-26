from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from .forms import PacienteForm, SesionForm
from .models import Paciente, Sesion



@login_required
def listar_pacientes(request):
    pacientes = Paciente.objects.order_by("codigo")
    return render(request, "pacientes/lista.html", {"pacientes": pacientes})


@login_required
def registrar_paciente(request):
    if request.method == "POST":
        form = PacienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Paciente registrado exitosamente.")
            return redirect("pacientes:lista")
    else:
        form = PacienteForm()
    return render(request, "pacientes/registrar.html", {"form": form})


@login_required
def listar_sesiones(request):
    sesiones = Sesion.objects.select_related("paciente")
    contexto = {
        "activas": sesiones.filter(fin__isnull=True).order_by("estacion"),
        "cerradas": sesiones.filter(fin__isnull=False).order_by("-fin"),
    }
    return render(request, "pacientes/sesiones.html", contexto)


@login_required
def iniciar_sesion_dialisis(request):
    if request.method == "POST":
        form = SesionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Sesión iniciada.")
            return redirect("pacientes:sesiones")
    else:
        form = SesionForm()
    return render(request, "pacientes/iniciar_sesion.html", {"form": form})


@login_required
@require_POST
def cerrar_sesion_dialisis(request, pk):
    sesion = get_object_or_404(Sesion, pk=pk, fin__isnull=True)
    sesion.fin = timezone.now()
    sesion.save(update_fields=["fin"])
    messages.success(request, "Sesión cerrada.")
    return redirect("pacientes:sesiones")