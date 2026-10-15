from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import PacienteForm
from .models import Paciente


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