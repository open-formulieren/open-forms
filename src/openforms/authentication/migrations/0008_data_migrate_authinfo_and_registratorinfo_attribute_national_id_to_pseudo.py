from django.db import migrations
from django.db.migrations.state import StateApps

import structlog

from openforms.authentication.constants import AuthAttribute

logger = structlog.stdlib.get_logger(__name__)


def convert_authinfo_and_registratorinfo_attribute_national_id_to_pseudo(
    apps: StateApps, _
):
    AuthInfo = apps.get_model("of_authentication", "AuthInfo")
    RegistratorInfo = apps.get_model("of_authentication", "RegistratorInfo")

    auth_info_to_update = []
    registrator_info_to_update = []

    for auth_info in AuthInfo.objects.filter(attribute="national_id"):
        auth_info.attribute = AuthAttribute.pseudo
        auth_info_to_update.append(auth_info)

    for registrator_info in RegistratorInfo.objects.filter(attribute="national_id"):
        registrator_info.attribute = AuthAttribute.pseudo
        registrator_info_to_update.append(registrator_info)

    AuthInfo.objects.bulk_update(auth_info_to_update, fields=["attribute"])
    RegistratorInfo.objects.bulk_update(
        registrator_info_to_update, fields=["attribute"]
    )


class Migration(migrations.Migration):
    dependencies = [
        ("of_authentication", "0007_alter_authinfo_id_alter_registratorinfo_id"),
    ]

    operations = [
        # we cannot reverse it since we don't know anymore which fields used national_id
        migrations.RunPython(
            convert_authinfo_and_registratorinfo_attribute_national_id_to_pseudo,
            migrations.RunPython.noop,
        ),
    ]
