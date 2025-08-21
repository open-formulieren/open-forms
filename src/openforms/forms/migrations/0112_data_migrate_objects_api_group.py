from django.db import migrations
from django.db.migrations.state import StateApps

import structlog

logger = structlog.stdlib.get_logger(__name__)


def convert_objects_api_group_pk_to_slug(apps: StateApps, _):
    FormRegistrationBackend = apps.get_model("forms", "FormRegistrationBackend")
    ObjectsAPIGroupConfig = apps.get_model("objects_api", "ObjectsAPIGroupConfig")

    objects_api_pk_to_slug = {
        group.pk: group.identifier for group in ObjectsAPIGroupConfig.objects.all()
    }
    registration_backends_to_update = []

    for registration_backend in FormRegistrationBackend.objects.exclude(
        options__objects_api_group__isnull=True
    ):
        api_group_pk = registration_backend.options["objects_api_group"]
        if api_group_pk not in objects_api_pk_to_slug:
            logger.warning(
                "migration_objects_api_group_not_found",
                form_uuid=registration_backend.form.uuid,
                objects_api_group=api_group_pk,
            )
            continue

        registration_backend.options["objects_api_group"] = objects_api_pk_to_slug[
            api_group_pk
        ]
        registration_backends_to_update.append(registration_backend)

    FormRegistrationBackend.objects.bulk_update(
        registration_backends_to_update, fields=["options"]
    )


def reverse_objects_api_group_slug_to_pk(apps: StateApps, _):
    FormRegistrationBackend = apps.get_model("forms", "FormRegistrationBackend")
    ObjectsAPIGroupConfig = apps.get_model("objects_api", "ObjectsAPIGroupConfig")

    objects_api_slug_to_pk = {
        group.identifier: group.pk for group in ObjectsAPIGroupConfig.objects.all()
    }
    registration_backends_to_update = []

    for registration_backend in FormRegistrationBackend.objects.exclude(
        options__objects_api_group__isnull=True
    ):
        api_group_slug = registration_backend.options["objects_api_group"]
        if api_group_slug not in objects_api_slug_to_pk:
            logger.warning(
                "migration_objects_api_group_not_found",
                form_uuid=registration_backend.form.uuid,
                objects_api_group=api_group_slug,
            )
            continue

        registration_backend.options["objects_api_group"] = objects_api_slug_to_pk[
            api_group_slug
        ]
        registration_backends_to_update.append(registration_backend)

    FormRegistrationBackend.objects.bulk_update(
        registration_backends_to_update, fields=["options"]
    )


class Migration(migrations.Migration):
    dependencies = [
        (
            "forms",
            "0111_formvariable_form_variable_subtype_empty_iff_data_type_is_not_array_and_more",
        ),
        ("objects_api", "0006_alter_objectsapigroupconfig_catalogue_domain"),
    ]

    operations = [
        migrations.RunPython(
            convert_objects_api_group_pk_to_slug,
            reverse_objects_api_group_slug_to_pk,
        ),
    ]
