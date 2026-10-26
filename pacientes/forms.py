from django import forms
from .models import Paciente, Sesion

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


class SesionForm(forms.ModelForm):
    class Meta:
        model = Sesion
        fields = ["paciente", "estacion"]
        labels = {"paciente": "Paciente", "estacion": "Estación"}
        error_messages = {
            "paciente": {"required": "Seleccione un paciente."},
            "estacion": {"required": "La estación es obligatoria."},
        }

    def clean_estacion(self):
        estacion = self.cleaned_data["estacion"].strip().upper()
        if Sesion.objects.filter(estacion=estacion, fin__isnull=True).exists():
            raise forms.ValidationError("La estación ya tiene una sesión activa.")
        return estacion

    def clean_paciente(self):
        paciente = self.cleaned_data["paciente"]
        if Sesion.objects.filter(paciente=paciente, fin__isnull=True).exists():
            raise forms.ValidationError(
                "El paciente ya tiene una sesión activa en otra estación."
            )
        return paciente