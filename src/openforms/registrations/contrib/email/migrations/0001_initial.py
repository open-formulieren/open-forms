# Generated by Django 3.2.12 on 2022-02-22 10:20

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="EmailConfig",
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
                    "attach_files_to_email",
                    models.BooleanField(
                        default=False,
                        help_text="Enable to attach file uploads to the registration email. Note that this is the global default which may be overridden per form. Form designers should take special care to ensure that the total file upload sizes do not exceed the email size limit.",
                        verbose_name="attach files to email",
                    ),
                ),
            ],
            options={
                "verbose_name": "Email registration configuration",
            },
        ),
    ]
