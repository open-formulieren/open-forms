# Generated by Django 4.2.17 on 2024-12-27 15:05

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("forms", "0097_v267_to_v270"),
        ("registrations_objects_api", "0001_initial_to_v267"),
        ("zgw_consumers", "0020_service_timeout"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="objectsapiconfig",
            name="catalogi_service",
        ),
        migrations.RemoveField(
            model_name="objectsapiconfig",
            name="drc_service",
        ),
        migrations.RemoveField(
            model_name="objectsapiconfig",
            name="informatieobjecttype_attachment",
        ),
        migrations.RemoveField(
            model_name="objectsapiconfig",
            name="informatieobjecttype_submission_csv",
        ),
        migrations.RemoveField(
            model_name="objectsapiconfig",
            name="informatieobjecttype_submission_report",
        ),
        migrations.RemoveField(
            model_name="objectsapiconfig",
            name="objects_service",
        ),
        migrations.RemoveField(
            model_name="objectsapiconfig",
            name="objecttype",
        ),
        migrations.RemoveField(
            model_name="objectsapiconfig",
            name="objecttype_version",
        ),
        migrations.RemoveField(
            model_name="objectsapiconfig",
            name="objecttypes_service",
        ),
        migrations.RemoveField(
            model_name="objectsapiconfig",
            name="organisatie_rsin",
        ),
    ]
