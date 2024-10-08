# Generated by Django 4.2.16 on 2024-09-11 14:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("zgw_consumers", "0020_service_timeout"),
        (
            "registrations_objects_api",
            "0023_alter_objectsapigroupconfig_catalogue_domain",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="objectsapigroupconfig",
            name="catalogi_service",
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={"api_type": "ztc"},
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="+",
                to="zgw_consumers.service",
                verbose_name="Catalogi API",
            ),
        ),
        migrations.AlterField(
            model_name="objectsapigroupconfig",
            name="drc_service",
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={"api_type": "drc"},
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="+",
                to="zgw_consumers.service",
                verbose_name="Documenten API",
            ),
        ),
    ]
