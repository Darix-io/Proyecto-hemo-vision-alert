from django.urls import path

from . import views

app_name = "monitoreo"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("estaciones/<str:codigo>/", views.detalle_estacion, name="detalle_estacion"),
]