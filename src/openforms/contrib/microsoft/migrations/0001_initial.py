# Generated by Django 2.2.24 on 2021-11-11 10:48

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="MSGraphService",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "label",
                    models.CharField(
                        help_text="Human readable label to identify services",
                        max_length=100,
                        verbose_name="label",
                    ),
                ),
                (
                    "tenant_id",
                    models.CharField(
                        help_text="Tenant ID", max_length=64, verbose_name="tenant ID"
                    ),
                ),
                (
                    "client_id",
                    models.CharField(
                        help_text="Client ID (sometimes called App ID or Application ID",
                        max_length=64,
                        verbose_name="client ID",
                    ),
                ),
                (
                    "secret",
                    models.CharField(
                        help_text="Secret for this Client ID",
                        max_length=64,
                        verbose_name="secret",
                    ),
                ),
            ],
            options={
                "verbose_name": "Microsoft Graph Service",
            },
        ),
    ]
