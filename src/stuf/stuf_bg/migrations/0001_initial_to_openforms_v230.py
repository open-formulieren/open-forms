# Generated by Django 3.2.20 on 2023-09-11 13:32

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("stuf", "0001_initial_pre_openforms_v230"),
    ]

    operations = [
        migrations.CreateModel(
            name="StufBGConfig",
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
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="stuf.stufservice",
                    ),
                ),
            ],
            options={
                "abstract": False,
                "verbose_name": "StUF-BG configuration",
            },
        ),
    ]
