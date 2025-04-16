# Generated by Django 3.2.23 on 2023-11-29 16:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("zgw_consumers", "0019_alter_service_uuid"),
    ]

    operations = [
        migrations.CreateModel(
            name="BRKConfig",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "service",
                    models.OneToOneField(
                        help_text="Service for API interaction with the BRK.",
                        limit_choices_to={"api_type": "orc"},
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="zgw_consumers.service",
                        verbose_name="BRK API",
                    ),
                ),
            ],
            options={
                "verbose_name": "BRK configuration",
            },
        ),
    ]
