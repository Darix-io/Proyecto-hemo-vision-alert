import django.db.models.deletion
from django.db import migrations, models


def textos_a_estaciones(apps, schema_editor):
    Sesion = apps.get_model("pacientes", "Sesion")
    Estacion = apps.get_model("pacientes", "Estacion")
    for sesion in Sesion.objects.all():
        codigo = (sesion.estacion or "").strip().upper()
        estacion, _ = Estacion.objects.get_or_create(codigo=codigo)
        sesion.estacion_nueva = estacion
        sesion.save(update_fields=["estacion_nueva"])


class Migration(migrations.Migration):

    dependencies = [
        ("pacientes", "0003_estacion"),
    ]

    operations = [
        migrations.AddField(
            model_name="sesion",
            name="estacion_nueva",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="sesiones",
                to="pacientes.estacion",
            ),
        ),
        migrations.RunPython(textos_a_estaciones, migrations.RunPython.noop),
        migrations.RemoveConstraint(
            model_name="sesion",
            name="una_sesion_activa_por_estacion",
        ),
        migrations.RemoveField(model_name="sesion", name="estacion"),
        migrations.RenameField(
            model_name="sesion", old_name="estacion_nueva", new_name="estacion"
        ),
        migrations.AlterField(
            model_name="sesion",
            name="estacion",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="sesiones",
                to="pacientes.estacion",
            ),
        ),
        migrations.AddConstraint(
            model_name="sesion",
            constraint=models.UniqueConstraint(
                condition=models.Q(("fin__isnull", True)),
                fields=("estacion",),
                name="una_sesion_activa_por_estacion",
            ),
        ),
    ]