from django.contrib.auth import views as auth_views
from django.urls import path

from .forms import InicioSesionForm

app_name = "seguridad"

urlpatterns = [
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="seguridad/login.html",
            authentication_form=InicioSesionForm,
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]