# Generated by Django 3.2.18 on 2023-03-29 14:31

from django.db import migrations
from django.db.models import Q


def move_email_registration_options(apps, schema_editor):
    Form = apps.get_model("forms", "Form")

    forms_to_update = Form.objects.filter(
        ~Q(registration_backend_options__email_subject=""), registration_backend="email"
    )
    for form in forms_to_update:
        form.registration_email_subject = form.registration_backend_options[
            "email_subject"
        ]

    Form.objects.bulk_update(forms_to_update, fields=["registration_email_subject"])


class Migration(migrations.Migration):

    dependencies = [
        ("forms", "0075_add_registration_email_fields"),
    ]

    operations = [
        migrations.RunPython(
            move_email_registration_options, migrations.RunPython.noop
        ),
    ]
