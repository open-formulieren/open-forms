# Generated by Django 2.2.24 on 2021-09-10 12:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("forms", "0003_formdefinition_internal_name"),
    ]

    operations = [
        migrations.RenameField(
            model_name="form",
            old_name="name",
            new_name="public_name",
        ),
    ]
