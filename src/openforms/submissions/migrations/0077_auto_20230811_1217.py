# Generated by Django 3.2.20 on 2023-08-11 10:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("submissions", "0076_alter_submission_form_url"),
    ]

    operations = [
        migrations.AddField(
            model_name="submission",
            name="cosign_statement_of_truth_accepted",
            field=models.BooleanField(
                default=False,
                help_text="Did the co-signer declare the form to be filled out truthfully?",
                verbose_name="cosign statement of truth accepted",
            ),
        ),
        migrations.AddField(
            model_name="submission",
            name="statement_of_truth_accepted",
            field=models.BooleanField(
                default=False,
                help_text="Did the user declare the form to be filled out truthfully?",
                verbose_name="statement of truth accepted",
            ),
        ),
    ]