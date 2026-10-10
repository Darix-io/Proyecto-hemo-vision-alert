from django import forms
from .models import Paciente

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = ["codigo"]
        labels = {"codigo": "Código del paciente"}
        error_messages = {
            "codigo": {
                "required": "El código es obligatorio.",
                "unique": "Ya existe un paciente con este codigo."
            }
        } 