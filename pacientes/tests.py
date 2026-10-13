from django.test import TestCase
from django.urls import reverse

from .models import Paciente


class RegistroPacienteTests(TestCase):
    def test_lista_vacia(self):
        respuesta = self.client.get(reverse("pacientes:lista"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(respuesta.context["pacientes"]), 0)

    def test_registra_dos_codigos_distintos_y_los_recupera(self):
        for codigo in ["PAC-001", "PAC-002"]:
            respuesta = self.client.post(
                reverse("pacientes:registrar"), {"codigo": codigo}
            )
            self.assertRedirects(respuesta, reverse("pacientes:lista"))
        self.assertEqual(Paciente.objects.count(), 2)
        respuesta = self.client.get(reverse("pacientes:lista"))
        self.assertContains(respuesta, "PAC-001")
        self.assertContains(respuesta, "PAC-002")

    def test_muestra_mensaje_al_registrar(self):
        respuesta = self.client.post(
            reverse("pacientes:registrar"), {"codigo": "PAC-001"}, follow=True
        )
        mensajes = [str(m) for m in respuesta.context["messages"]]
        self.assertTrue(any("registrado" in m for m in mensajes))

    def test_rechaza_codigo_vacio(self):
        respuesta = self.client.post(reverse("pacientes:registrar"), {"codigo": "   "})
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("codigo", respuesta.context["form"].errors)
        self.assertEqual(Paciente.objects.count(), 0)

    def test_rechaza_codigo_duplicado(self):
        Paciente.objects.create(codigo="PAC-001")
        respuesta = self.client.post(
            reverse("pacientes:registrar"), {"codigo": "PAC-001"}
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("codigo", respuesta.context["form"].errors)
        self.assertEqual(Paciente.objects.count(), 1)