from django.urls import path

from . import api

app_name = "riesgo"

urlpatterns = [
    path("senal/", api.senal, name="senal"),
    path("evento/", api.evento, name="evento"),
]