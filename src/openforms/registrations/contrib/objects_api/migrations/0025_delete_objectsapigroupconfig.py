# Generated by Django 4.2.16 on 2024-09-12 17:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        (
            "registrations_objects_api",
            "0024_alter_objectsapigroupconfig_catalogi_service_and_more",
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.DeleteModel(
                    name="ObjectsAPIGroupConfig",
                ),
            ],
        )
    ]
