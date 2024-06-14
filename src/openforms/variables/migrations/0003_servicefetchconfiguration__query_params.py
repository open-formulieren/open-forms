# Generated by Django 3.2.18 on 2023-03-13 15:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("variables", "0002_servicefetchconfiguration_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="servicefetchconfiguration",
            name="_query_params",
            field=models.JSONField(
                blank=True, default=dict, verbose_name="HTTP query string"
            ),
        ),
    ]