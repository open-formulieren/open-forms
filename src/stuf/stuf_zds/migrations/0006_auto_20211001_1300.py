# Generated by Django 2.2.24 on 2021-10-01 11:00

from django.db import migrations, models
import django.db.models.deletion


def migrate_services(apps, _):
    StufService = apps.get_model("stuf", "StufService")
    StufZDSConfig = apps.get_model("stuf_zds", "StufZDSConfig")

    try:
        stuf_zds_config = StufZDSConfig.objects.get()  # There can be only one (or none)
        stuf_zds_config.new_service = StufService.objects.get(
            soap_service=stuf_zds_config.old_service
        )
        stuf_zds_config.save()
    except StufZDSConfig.DoesNotExist:
        # This config has not been created, no need to migrate anything
        pass
    except StufService.DoesNotExist:
        # There was no service, no need to migrate anything
        pass


class Migration(migrations.Migration):

    dependencies = [
        ("stuf", "0008_auto_20210927_1555"),
        ("stuf_zds", "0005_stufzdsconfig_zds_zaaktype_status_omschrijving"),
    ]

    operations = [
        migrations.RenameField(
            model_name="stufzdsconfig",
            old_name="service",
            new_name="old_service",
        ),
        migrations.AddField(
            model_name="stufzdsconfig",
            name="new_service",
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="stuf_zds_config",
                to="stuf.StufService",
            ),
        ),
        migrations.RunPython(migrate_services, migrations.RunPython.noop),
        migrations.RenameField(
            model_name="stufzdsconfig",
            old_name="new_service",
            new_name="service",
        ),
        migrations.RemoveField(
            model_name="stufzdsconfig",
            name="old_service",
        ),
    ]
