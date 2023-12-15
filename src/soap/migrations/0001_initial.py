# Generated by Django 3.2.20 on 2023-07-18 08:36

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("simple_certmanager", "0002_alter_certificate_private_key_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="SoapService",
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
                    "url",
                    models.URLField(
                        blank=True,
                        help_text="URL of the service to connect to.",
                        verbose_name="URL",
                    ),
                ),
                (
                    "soap_version",
                    models.CharField(
                        choices=[
                            ("1.1", "SOAP 1.1"),
                            ("1.2", "SOAP 1.2"),
                        ],
                        default="1.2",
                        help_text="The SOAP version to use for the message envelope.",
                        max_length=5,
                        verbose_name="SOAP version",
                    ),
                ),
                (
                    "endpoint_security",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("basicauth", "Basic authentication"),
                            ("wss", "SOAP extension: WS-Security"),
                            ("wss_basicauth", "Both"),
                        ],
                        help_text="The security to use for messages sent to the endpoints.",
                        max_length=20,
                        verbose_name="Security",
                    ),
                ),
                (
                    "user",
                    models.CharField(
                        blank=True,
                        help_text="Username to use in the XML security context.",
                        max_length=200,
                        verbose_name="user",
                    ),
                ),
                (
                    "password",
                    models.CharField(
                        blank=True,
                        help_text="Password to use in the XML security context.",
                        max_length=200,
                        verbose_name="password",
                    ),
                ),
                (
                    "client_certificate",
                    models.ForeignKey(
                        blank=True,
                        help_text="The SSL certificate file used for client identification. If left empty, mutual TLS is disabled.",
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="soap_services_client",
                        to="simple_certmanager.certificate",
                    ),
                ),
                (
                    "server_certificate",
                    models.ForeignKey(
                        blank=True,
                        help_text="The SSL/TLS certificate of the server",
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="soap_services_server",
                        to="simple_certmanager.certificate",
                    ),
                ),
            ],
            options={
                "verbose_name": "SOAP service",
                "verbose_name_plural": "SOAP services",
            },
        ),
    ]