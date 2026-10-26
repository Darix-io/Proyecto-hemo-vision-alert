from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class InicioYCierreDeSesionTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="enfermeria", password="clave-de-prueba-123"
        )
        self.datos_validos = {
            "username": "enfermeria",
            "password": "clave-de-prueba-123",
        }

    def test_credenciales_validas_abren_sesion(self):
        respuesta = self.client.post(reverse("seguridad:login"), self.datos_validos)
        self.assertRedirects(respuesta, reverse("pacientes:lista"))
        self.assertIn("_auth_user_id", self.client.session)

    def test_credenciales_invalidas_no_abren_sesion(self):
        respuesta = self.client.post(
            reverse("seguridad:login"),
            {"username": "enfermeria", "password": "otra-clave"},
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Credenciales incorrectas.")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_cuenta_inactiva_no_puede_entrar(self):
        self.usuario.is_active = False
        self.usuario.save()
        respuesta = self.client.post(reverse("seguridad:login"), self.datos_validos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_sin_sesion_se_redirige_al_login(self):
        respuesta = self.client.get(reverse("pacientes:lista"))
        destino = f"{reverse('seguridad:login')}?next={reverse('pacientes:lista')}"
        self.assertRedirects(respuesta, destino)

    def test_tras_cerrar_sesion_no_se_consultan_datos(self):
        self.client.force_login(self.usuario)
        self.client.post(reverse("seguridad:logout"))
        respuesta = self.client.get(reverse("pacientes:lista"))
        self.assertEqual(respuesta.status_code, 302)
        self.assertNotIn("_auth_user_id", self.client.session)