# Generated by Django 4.2.14 on 2024-07-22 15:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("submissions", "0008_submission_initial_data_reference"),
    ]

    operations = [
        # RunPython operation removed as part of 3.0 release cycle - these migrations are
        # guaranteed to have been executed on Open Forms 2.8.x for existing instances.
        migrations.AddConstraint(
            model_name="submission",
            constraint=models.CheckConstraint(
                check=models.Q(
                    ("finalised_registration_backend_key", ""),
                    models.Q(
                        models.Q(
                            ("finalised_registration_backend_key", ""), _negated=True
                        ),
                        ("completed_on__isnull", False),
                    ),
                    _connector="OR",
                ),
                name="only_completed_submission_has_finalised_registration_backend_key",
                violation_error_message="Only completed submissions may persist a finalised registration backend key.",
            ),
        ),
    ]
