# Generated by Django 4.2.16 on 2024-11-19 11:23

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("objects_api", "0002_objectsapigroupconfig_identifier"),
    ]

    operations = [
        migrations.AlterField(
            model_name="objectsapigroupconfig",
            name="identifier",
            field=models.SlugField(
                help_text="A unique, human-friendly identifier to identify this group.",
                unique=True,
                verbose_name="identifier",
            ),
        ),
    ]
