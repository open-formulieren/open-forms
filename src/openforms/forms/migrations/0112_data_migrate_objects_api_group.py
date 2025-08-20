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
        if (
            registration_backend.options["objects_api_group"]
            not in objects_api_pk_to_slug
        ):
            logger.warning(
                "migration_objects_api_group_not_found",
                form=registration_backend.form,
                objects_api_group=registration_backend.options["objects_api_group"],
            )
            continue

        options = registration_backend.options
        options["objects_api_group"] = objects_api_pk_to_slug[
            options["objects_api_group"]
        ]
        registration_backend.options = options

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
        if (
            registration_backend.options["objects_api_group"]
            not in objects_api_slug_to_pk
        ):
            logger.warning(
                "migration_objects_api_group_not_found",
                form=registration_backend.form,
                objects_api_group=registration_backend.options["objects_api_group"],
            )
            continue

        options = registration_backend.options
        options["objects_api_group"] = objects_api_slug_to_pk[
            options["objects_api_group"]
        ]
        registration_backend.options = options

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
