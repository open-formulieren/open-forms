# Generated by Django 4.2.20 on 2025-03-31 14:06

from django.db import migrations
from django.db.migrations.state import StateApps
from django.utils.module_loading import import_string

from openforms.upgrades.upgrade_paths import setup_scripts_env


class FixScript:
    def __init__(self, name: str):
        with setup_scripts_env():
            self.callback = import_string(f"{name}.main")

    def __call__(self, apps: StateApps, _):
        self.callback(skip_setup=True)


class Migration(migrations.Migration):

    dependencies = [
        ("forms", "0101_fix_radio_empty_default_value"),
    ]

    operations = [
        migrations.RunPython(
            FixScript("fix_objects_api_form_registration_variables_mapping"),
            migrations.RunPython.noop,
        ),
        migrations.RunPython(
            FixScript("fix_selectboxes_component_default_values"),
            migrations.RunPython.noop,
        ),
    ]
