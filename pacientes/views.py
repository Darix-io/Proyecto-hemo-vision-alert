from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from .forms import PacienteForm, SesionForm
from .models import Paciente, Sesion
from monitoreo.servicios import construir_tablero
from django.core.paginator import Paginator


@login_required
def listar_pacientes(request):
    q = request.GET.get("q", "").strip()
    sala = request.GET.get("sala", "")
    estado = request.GET.get("estado", "")
    pacientes = Paciente.objects.order_by("codigo")
    if q:
        pacientes = pacientes.filter(codigo__icontains=q)
    tablero = construir_tablero()
    por_codigo = {}
    for s in tablero["salas"]:
        for t in s["tarjetas"]:
            if t["paciente"]:
                por_codigo[t["paciente"]] = t
    filas = [{"codigo": p.codigo, "tarjeta": por_codigo.get(p.codigo)} for p in pacientes]
    if sala:
        filas = [f for f in filas if f["tarjeta"] and f["tarjeta"]["sala"] == sala]
    if estado == "sin_sesion":
        filas = [f for f in filas if not f["tarjeta"]]
    elif estado:
        filas = [f for f in filas if f["tarjeta"] and f["tarjeta"]["estado"] == estado]
    pagina = Paginator(filas, 10).get_page(request.GET.get("pagina"))
    parametros = request.GET.copy()
    parametros.pop("pagina", None)
    return render(
        request,
        "pacientes/lista.html",
        {
            "pacientes": pacientes,
            "pagina": pagina,
            "total": Paciente.objects.count(),
            "q": q,
            "sala": sala,
            "estado": estado,
            "salas": tablero["nombres_salas"],
            "filtrado": bool(q or sala or estado),
            "consulta": parametros.urlencode(),
        },
    )

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