# Generated by Django 4.2.16 on 2024-12-02 10:30

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("zgw_apis", "0015_explicit_objects_api_groups"),
    ]

    operations = [
        migrations.AddField(
            model_name="zgwapigroupconfig",
            name="identifier",
            field=models.SlugField(
                blank=True,
                help_text="A unique, human-friendly identifier to identify this group.",
                verbose_name="identifier",
            ),
        ),
        # RunPython operation removed as it's guaranteed to have been executed as part of
        # the 3.0 upgrade cycle.
    ]
