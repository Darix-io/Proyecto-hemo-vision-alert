from django.urls import path
from . import views

app_name = "pacientes"

urlpatterns = [
    path("", views.listar_pacientes, name = "lista"),
    path("registrar/", views.registrar_paciente, name = "registrar"),
    path("sesiones/", views.listar_sesiones, name="sesiones"),
    path("sesiones/iniciar/", views.iniciar_sesion_dialisis, name="sesion_iniciar"),
    path("sesiones/<int:pk>/cerrar/", views.cerrar_sesion_dialisis, name="sesion_cerrar"),
]