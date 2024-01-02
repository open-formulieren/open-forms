# Generated by Django 3.2.20 on 2023-08-16 09:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("forms", "0089_enable_mutiple_registration_backends"),
    ]

    operations = [
        migrations.AddField(
            model_name="form",
            name="ask_privacy_consent",
            field=models.CharField(
                choices=[
                    ("global_setting", "Global setting"),
                    ("required", "Required"),
                    ("disabled", "Disabled"),
                ],
                default="global_setting",
                help_text="If enabled, the user will have to agree to the privacy policy before submitting a form.",
                max_length=50,
                verbose_name="ask privacy consent",
            ),
        ),
        migrations.AddField(
            model_name="form",
            name="ask_statement_of_truth",
            field=models.CharField(
                choices=[
                    ("global_setting", "Global setting"),
                    ("required", "Required"),
                    ("disabled", "Disabled"),
                ],
                default="global_setting",
                help_text="If enabled, the user will have to agree that they filled out the form truthfully before submitting it.",
                max_length=50,
                verbose_name="ask statement of truth",
            ),
        ),
    ]