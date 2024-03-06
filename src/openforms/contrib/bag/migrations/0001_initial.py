# Generated by Django 2.2.20 on 2021-07-19 08:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("zgw_consumers", "0012_auto_20210104_1039"),
    ]

    operations = [
        migrations.CreateModel(
            name="BAGConfig",
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
                    "bag_service",
                    models.ForeignKey(
                        help_text="Select which service to use for the BAG API.",
                        limit_choices_to={"api_type": "orc"},
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="zgw_consumers.Service",
                        verbose_name="BAG service",
                    ),
                ),
            ],
            options={
                "verbose_name": "BAG configuration",
            },
        ),
    ]