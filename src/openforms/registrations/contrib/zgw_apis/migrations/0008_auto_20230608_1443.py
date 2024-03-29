# Generated by Django 3.2.19 on 2023-06-08 12:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("zgw_apis", "0007_move_singleton_data"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="zgwconfig",
            name="auteur",
        ),
        migrations.RemoveField(
            model_name="zgwconfig",
            name="doc_vertrouwelijkheidaanduiding",
        ),
        migrations.RemoveField(
            model_name="zgwconfig",
            name="drc_service",
        ),
        migrations.RemoveField(
            model_name="zgwconfig",
            name="informatieobjecttype",
        ),
        migrations.RemoveField(
            model_name="zgwconfig",
            name="organisatie_rsin",
        ),
        migrations.RemoveField(
            model_name="zgwconfig",
            name="zaak_vertrouwelijkheidaanduiding",
        ),
        migrations.RemoveField(
            model_name="zgwconfig",
            name="zaaktype",
        ),
        migrations.RemoveField(
            model_name="zgwconfig",
            name="zrc_service",
        ),
        migrations.RemoveField(
            model_name="zgwconfig",
            name="ztc_service",
        ),
        migrations.AddField(
            model_name="zgwconfig",
            name="default_zgw_api_group",
            field=models.ForeignKey(
                help_text="Which set of ZGW APIs should be used as default.",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="zgw_apis.zgwapigroupconfig",
                verbose_name="default ZGW API set.",
            ),
        ),
    ]
