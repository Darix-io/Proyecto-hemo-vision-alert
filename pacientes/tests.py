from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Paciente


class RegistroPacienteTests(TestCase):
    def setUp(self):
        usuario = get_user_model().objects.create_user(
            username="enfermeria", password="clave-de-prueba-123"
        )
        self.client.force_login(usuario)

    def test_lista_vacia(self):
        respuesta = self.client.get(reverse("pacientes:lista"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Todavía no hay pacientes registrados.")

    def test_registra_dos_codigos_distintos_y_los_recupera(self):
        self.client.post(reverse("pacientes:registrar"), {"codigo": "P01"})
        self.client.post(reverse("pacientes:registrar"), {"codigo": "P02"})
        respuesta = self.client.get(reverse("pacientes:lista"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "P01")
        self.assertContains(respuesta, "P02")

    def test_muestra_mensaje_al_registrar(self):
        respuesta = self.client.post(
            reverse("pacientes:registrar"), {"codigo": "P01"}, follow=True
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Paciente registrado exitosamente.")

    def test_rechaza_codigo_vacio(self):
        respuesta = self.client.post(reverse("pacientes:registrar"), {"codigo": ""})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Paciente.objects.count(), 0)

    def test_rechaza_codigo_duplicado(self):
        self.client.post(reverse("pacientes:registrar"), {"codigo": "P01"})
        respuesta = self.client.post(reverse("pacientes:registrar"), {"codigo": "P01"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Paciente.objects.count(), 1)