# Generated by Django 4.2.18 on 2025-03-20 08:43

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("haalcentraal", "0003_auto_20240115_1528"),
    ]

    operations = [
        migrations.AddField(
            model_name="haalcentraalconfig",
            name="brp_personen_oin_header_name",
            field=models.CharField(
                default="x-origin-oin",
                help_text="The header name that will be used to pass the organization identification number (OIN).",
                max_length=100,
                verbose_name="header name for OIN value",
            ),
        ),
    ]
