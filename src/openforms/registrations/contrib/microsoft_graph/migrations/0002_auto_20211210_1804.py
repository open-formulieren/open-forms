# Generated by Django 2.2.25 on 2021-12-10 17:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("registrations_microsoft_graph", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="msgraphregistrationconfig",
            name="service",
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="registration_config",
                to="microsoft.MSGraphService",
                verbose_name="Microsoft Graph service",
            ),
        ),
    ]
