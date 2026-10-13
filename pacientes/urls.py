from django.urls import path
from . import views

app_name = "pacientes"

urlpatterns = [
    path("", views.listar_pacientes, name = "lista"),
    path("registrar/", views.registrar_paciente, name = "registrar"),
]