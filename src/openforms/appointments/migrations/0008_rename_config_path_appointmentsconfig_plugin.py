# Generated by Django 3.2.16 on 2023-01-11 14:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("appointments", "0007_alter_appointmentsconfig_config_path"),
    ]

    operations = [
        migrations.RenameField(
            model_name="appointmentsconfig",
            old_name="config_path",
            new_name="plugin",
        ),
    ]