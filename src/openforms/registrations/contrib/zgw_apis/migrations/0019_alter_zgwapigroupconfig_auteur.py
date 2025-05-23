# Generated by Django 4.2.18 on 2025-01-27 15:41

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("zgw_apis", "0018_alter_zgwapigroupconfig_drc_service_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="zgwapigroupconfig",
            name="auteur",
            field=models.CharField(
                default="Aanvrager",
                help_text="The value of the `author` field for documents that will be created in Documenten API.",
                max_length=200,
                verbose_name="auteur",
            ),
        ),
    ]
