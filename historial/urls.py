from django.urls import path

from . import views

app_name = "historial"

urlpatterns = [
    path("", views.historial, name="lista"),
    path("informe.csv", views.informe, name="informe"),
    path("eliminar/<int:pk>/", views.eliminar, name="eliminar"),
    path("vaciar/", views.vaciar, name="vaciar"),
]
