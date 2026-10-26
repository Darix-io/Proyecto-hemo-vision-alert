from django.contrib.auth.forms import AuthenticationForm


class InicioSesionForm(AuthenticationForm):
    error_messages = {
        "invalid_login": "Credenciales incorrectas.",
        "inactive": "Credenciales incorrectas.",
    }