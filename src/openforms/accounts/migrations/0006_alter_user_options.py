# Generated by Django 3.2.15 on 2022-09-02 07:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0005_auto_20211216_1550"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="user",
            options={
                "permissions": (
                    ("email_backend_test", "Can use email backend test"),
                    ("configuration_overview", "Can access configuration overview"),
                    (
                        "can_navigate_between_submission_steps",
                        "Can navigate between submission steps",
                    ),
                ),
                "verbose_name": "user",
                "verbose_name_plural": "users",
            },
        ),
    ]
