# Generated by Django 3.2.20 on 2023-09-08 10:02

import django.core.serializers.json
import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models

import openforms.appointments.fields


class Migration(migrations.Migration):
    dependencies = [
        ("submissions", "0001_initial_to_openforms_v230"),
    ]

    operations = [
        migrations.CreateModel(
            name="AppointmentInfo",
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
                    "status",
                    models.CharField(
                        choices=[
                            ("success", "Success"),
                            (
                                "missing_info",
                                "Submission does not contain all the info needed to make an appointment",
                            ),
                            ("failed", "Failed"),
                            ("cancelled", "Cancelled"),
                        ],
                        max_length=50,
                        verbose_name="status",
                    ),
                ),
                (
                    "appointment_id",
                    models.CharField(
                        blank=True, max_length=64, verbose_name="appointment ID"
                    ),
                ),
                (
                    "error_information",
                    models.TextField(blank=True, verbose_name="error information"),
                ),
                (
                    "submission",
                    models.OneToOneField(
                        help_text="The submission that made the appointment",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="appointment_info",
                        to="submissions.submission",
                    ),
                ),
                (
                    "start_time",
                    models.DateTimeField(
                        blank=True,
                        help_text="Start time of the appointment",
                        null=True,
                        verbose_name="start time",
                    ),
                ),
                (
                    "created",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when the appointment details were created",
                        verbose_name="created",
                    ),
                ),
            ],
            options={
                "verbose_name": "Appointment information",
                "verbose_name_plural": "Appointment information",
            },
        ),
        migrations.CreateModel(
            name="AppointmentsConfig",
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
                    "plugin",
                    openforms.appointments.fields.AppointmentBackendChoiceField(
                        blank=True, max_length=100, verbose_name="appointment plugin"
                    ),
                ),
                (
                    "limit_to_location",
                    models.CharField(
                        blank=True,
                        help_text="If configured, only products connected to this location are exposed. Additionally, the user can only select this location for the appointment.",
                        max_length=50,
                        verbose_name="location",
                    ),
                ),
            ],
            options={
                "abstract": False,
                "verbose_name": "Appointment configuration",
            },
        ),
        migrations.CreateModel(
            name="Appointment",
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
                    "plugin",
                    openforms.appointments.fields.AppointmentBackendChoiceField(
                        help_text="The plugin active at the time of creation. This determines the context to interpret the submitted data.",
                        max_length=100,
                        verbose_name="plugin",
                    ),
                ),
                (
                    "location",
                    models.CharField(
                        help_text="Identifier of the location in the selected plugin.",
                        max_length=128,
                        verbose_name="location ID",
                    ),
                ),
                (
                    "datetime",
                    models.DateTimeField(
                        help_text="Date and time of the appointment",
                        verbose_name="appointment time",
                    ),
                ),
                (
                    "contact_details_meta",
                    models.JSONField(
                        default=list,
                        encoder=django.core.serializers.json.DjangoJSONEncoder,
                        help_text="Contact detail field definitions, depending on the required fields in the selected plugin. Recorded for historical purposes.",
                        verbose_name="contact details meta",
                    ),
                ),
                (
                    "contact_details",
                    models.JSONField(
                        default=dict,
                        encoder=django.core.serializers.json.DjangoJSONEncoder,
                        help_text="Additional contact detail field values.",
                        verbose_name="contact details",
                    ),
                ),
                (
                    "submission",
                    models.OneToOneField(
                        help_text="The submission that made the appointment",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="appointment",
                        to="submissions.submission",
                    ),
                ),
            ],
            options={
                "verbose_name": "appointment",
                "verbose_name_plural": "appointments",
            },
        ),
        migrations.CreateModel(
            name="AppointmentProduct",
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
                    "product_id",
                    models.CharField(
                        help_text="Identifier of the product in the selected plugin.",
                        max_length=128,
                        verbose_name="product ID",
                    ),
                ),
                (
                    "amount",
                    models.PositiveSmallIntegerField(
                        help_text="Number of times (amount of people) the product is ordered",
                        validators=[django.core.validators.MinValueValidator(1)],
                        verbose_name="amount",
                    ),
                ),
                (
                    "appointment",
                    models.ForeignKey(
                        help_text="Appointment for this product order.",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="products",
                        to="appointments.appointment",
                        verbose_name="appointment",
                    ),
                ),
            ],
            options={
                "verbose_name": "appointment product",
                "verbose_name_plural": "appointment products",
            },
        ),
    ]
