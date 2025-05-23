# Generated by Django 4.2.16 on 2024-11-19 11:11

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("objects_api", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="objectsapigroupconfig",
            name="identifier",
            field=models.SlugField(
                blank=True,
                help_text="A unique, human-friendly identifier to identify this group.",
                verbose_name="identifier",
            ),
        ),
        # RunPython operation removed as part of 3.1.0 release cycle. It's guaranteed
        # to have been executed during the 3.0.x upgrade.
    ]
