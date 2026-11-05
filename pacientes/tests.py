from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Estacion, Paciente, Sesion
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError


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


class SesionesTests(TestCase):
    def setUp(self):
        usuario = get_user_model().objects.create_user(
            username="enfermeria", password="clave-de-prueba-123"
        )
        self.client.force_login(usuario)
        self.p1 = Paciente.objects.create(codigo="PAC-001")
        self.p2 = Paciente.objects.create(codigo="PAC-002")
        self.e7 = Estacion.objects.create(codigo="EST-07", sala="Sala A")
        self.e8 = Estacion.objects.create(codigo="EST-08", sala="Sala A")
        self.e9 = Estacion.objects.create(codigo="EST-09", sala="Sala A")

    def iniciar(self, paciente, estacion):
        return self.client.post(
            reverse("pacientes:sesion_iniciar"),
            {"paciente": paciente.pk, "estacion": estacion.pk},
        )

    def test_lista_vacia_de_sesiones(self):
        respuesta = self.client.get(reverse("pacientes:sesiones"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "No hay sesiones activas.")

    def test_inicia_una_sesion(self):
        respuesta = self.iniciar(self.p1, self.e7)
        self.assertRedirects(respuesta, reverse("pacientes:sesiones"))
        sesion = Sesion.objects.get()
        self.assertEqual(sesion.paciente, self.p1)
        self.assertEqual(sesion.estacion, self.e7)
        self.assertIsNone(sesion.fin)

    def test_rechaza_estacion_ocupada(self):
        Sesion.objects.create(paciente=self.p1, estacion=self.e7)
        respuesta = self.iniciar(self.p2, self.e7)
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("estacion", respuesta.context["form"].errors)
        self.assertEqual(Sesion.objects.count(), 1)

    def test_rechaza_paciente_con_sesion_activa(self):
        Sesion.objects.create(paciente=self.p1, estacion=self.e7)
        respuesta = self.iniciar(self.p1, self.e9)
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("paciente", respuesta.context["form"].errors)
        self.assertEqual(Sesion.objects.count(), 1)

    def test_no_permite_estaciones_inactivas(self):
        self.e9.activa = False
        self.e9.save()
        respuesta = self.iniciar(self.p1, self.e9)
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("estacion", respuesta.context["form"].errors)
        self.assertEqual(Sesion.objects.count(), 0)

    def test_cierra_una_sesion_y_registra_el_fin(self):
        sesion = Sesion.objects.create(paciente=self.p1, estacion=self.e7)
        url = reverse("pacientes:sesion_cerrar", args=[sesion.pk])
        respuesta = self.client.post(url)
        self.assertRedirects(respuesta, reverse("pacientes:sesiones"))
        sesion.refresh_from_db()
        self.assertIsNotNone(sesion.fin)

    def test_la_estacion_queda_libre_al_cerrar(self):
        sesion = Sesion.objects.create(paciente=self.p1, estacion=self.e7)
        self.client.post(reverse("pacientes:sesion_cerrar", args=[sesion.pk]))
        respuesta = self.iniciar(self.p2, self.e7)
        self.assertRedirects(respuesta, reverse("pacientes:sesiones"))
        self.assertEqual(Sesion.objects.count(), 2)

    def test_cerrar_solo_acepta_post(self):
        sesion = Sesion.objects.create(paciente=self.p1, estacion=self.e7)
        url = reverse("pacientes:sesion_cerrar", args=[sesion.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        sesion.refresh_from_db()
        self.assertIsNone(sesion.fin)

    def test_no_se_cierra_dos_veces_una_sesion(self):
        sesion = Sesion.objects.create(paciente=self.p1, estacion=self.e7)
        url = reverse("pacientes:sesion_cerrar", args=[sesion.pk])
        self.client.post(url)
        self.assertEqual(self.client.post(url).status_code, 404)

    def test_conserva_el_vinculo_historico(self):
        sesion = Sesion.objects.create(paciente=self.p1, estacion=self.e7)
        self.client.post(reverse("pacientes:sesion_cerrar", args=[sesion.pk]))
        with self.assertRaises(ProtectedError):
            self.p1.delete()
        with self.assertRaises(ProtectedError):
            self.e7.delete()
        self.assertTrue(Sesion.objects.filter(pk=sesion.pk).exists())

    def test_la_base_impide_dos_sesiones_activas_del_paciente(self):
        Sesion.objects.create(paciente=self.p1, estacion=self.e7)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Sesion.objects.create(paciente=self.p1, estacion=self.e8)

    def test_la_base_impide_dos_sesiones_activas_en_la_estacion(self):
        Sesion.objects.create(paciente=self.p1, estacion=self.e7)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Sesion.objects.create(paciente=self.p2, estacion=self.e7)

    def test_exige_iniciar_sesion(self):
        self.client.logout()
        respuesta = self.client.get(reverse("pacientes:sesiones"))
        destino = f"{reverse('seguridad:login')}?next={reverse('pacientes:sesiones')}"
        self.assertRedirects(respuesta, destino)