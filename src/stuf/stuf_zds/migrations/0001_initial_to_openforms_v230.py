# Generated by Django 3.2.20 on 2023-09-11 13:35

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [
        ("stuf_zds", "0001_initial"),
        ("stuf_zds", "0002_nice_verbose_name"),
        ("stuf_zds", "0003_auto_20210604_1355"),
        ("stuf_zds", "0004_auto_20210624_2028"),
        ("stuf_zds", "0005_stufzdsconfig_zds_zaaktype_status_omschrijving"),
        ("stuf_zds", "0006_auto_20211001_1300"),
        ("stuf_zds", "0007_auto_20211230_1558"),
    ]

    dependencies = [
        ("stuf", "0008_auto_20210927_1555"),
    ]

    operations = [
        migrations.CreateModel(
            name="StufZDSConfig",
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
                    "gemeentecode",
                    models.CharField(
                        help_text="Municipality code to register zaken",
                        max_length=4,
                        validators=[
                            django.core.validators.RegexValidator(
                                message="Expected a numerical value.", regex="^[0-9]+$"
                            )
                        ],
                        verbose_name="Municipality code",
                    ),
                ),
                (
                    "service",
                    models.OneToOneField(
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="stuf_zds_config",
                        to="stuf.stufservice",
                    ),
                ),
            ],
            options={
                "abstract": False,
                "verbose_name": "StUF-ZDS configuration",
            },
        ),
    ]