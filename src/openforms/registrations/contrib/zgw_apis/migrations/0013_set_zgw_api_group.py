# Generated by Django 4.2.11 on 2024-06-26 10:03

from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.migrations.state import StateApps


def set_zgw_api_group(apps: StateApps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    """Change the ZGW registration options to always have a ZGW API group set."""

    FormRegistrationBackend = apps.get_model("forms", "FormRegistrationBackend")
    ZgwConfig = apps.get_model("zgw_apis", "ZgwConfig")
    ZGWApiGroupConfig = apps.get_model("zgw_apis", "ZGWApiGroupConfig")

    zgw_config = ZgwConfig.objects.first()
    if zgw_config is not None:
        default_group = zgw_config.default_zgw_api_group
    else:
        default_group = None

    for registration_backend in FormRegistrationBackend.objects.filter(
        backend="zgw-create-zaak"
    ):
        zgw_api_group = registration_backend.options.get("zgw_api_group")
        if zgw_api_group is None:
            if default_group is None:
                # This can only happen if upgrade checks were bypassed.
                default_group = ZGWApiGroupConfig.objects.create(
                    name="AUTO_GENERATED - FIXME"
                )

            registration_backend.options["zgw_api_group"] = default_group.pk
            registration_backend.save()


class Migration(migrations.Migration):

    dependencies = [
        ("zgw_apis", "0012_remove_zgwapigroupconfig_informatieobjecttype_and_more"),
        ("forms", "0100_add_default_objects_api_group"),
    ]

    operations = [
        migrations.RunPython(
            set_zgw_api_group,
            migrations.RunPython.noop,
        ),
    ]