# Generated by Django 2.2.13 on 2020-07-22 20:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("zgw_consumers", "0009_auto_20200401_0829"),
    ]

    operations = [
        migrations.CreateModel(
            name="NLXConfig",
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
                    "directory",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("demo", "Demo"),
                            ("preprod", "Pre-prod"),
                            ("prod", "Prod"),
                        ],
                        max_length=50,
                        verbose_name="NLX directory",
                    ),
                ),
                (
                    "outway",
                    models.URLField(
                        blank=True,
                        help_text="Example: http://my-outway.nlx:8080",
                        verbose_name="NLX outway address",
                    ),
                ),
            ],
            options={
                "verbose_name": "NLX configuration",
            },
        ),
    ]
