# Generated by Django 2.2.25 on 2022-01-06 11:39

from django.db import migrations, models

import openforms.emails.validators
import openforms.template.validators


class Migration(migrations.Migration):

    dependencies = [
        ("emails", "0006_auto_20211117_1729"),
    ]

    operations = [
        migrations.AlterField(
            model_name="confirmationemailtemplate",
            name="content",
            field=models.TextField(
                blank=True,
                help_text="The content of the email message can contain variables that will be templated from the submitted form data.",
                validators=[
                    openforms.template.validators.DjangoTemplateValidator(
                        required_template_tags=[
                            "appointment_information",
                            "payment_information",
                        ]
                    ),
                    openforms.emails.validators.URLSanitationValidator(),
                ],
                verbose_name="content",
            ),
        ),
    ]
