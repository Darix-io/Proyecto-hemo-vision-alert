from django.urls import path

from . import views

app_name = "monitoreo"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("estaciones/<str:codigo>/", views.detalle_estacion, name="detalle_estacion"),
    path("alertas/<int:pk>/", views.detalle_alerta, name="detalle_alerta"),
    path("revisiones/<int:pk>/", views.revision_resultado, name="revision_resultado"),
]