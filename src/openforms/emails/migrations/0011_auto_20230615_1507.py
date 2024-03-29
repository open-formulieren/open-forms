# Generated by Django 3.2.19 on 2023-06-15 13:07

from django.db import migrations, models
import openforms.emails.validators
import openforms.template.validators


class Migration(migrations.Migration):

    dependencies = [
        ("emails", "0010_add_cosign_templatetag"),
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
                        backend="openforms.template.openforms_backend",
                        required_template_tags=[
                            "appointment_information",
                            "payment_information",
                            "cosign_information",
                        ],
                    ),
                    openforms.emails.validators.URLSanitationValidator(),
                ],
                verbose_name="content",
            ),
        ),
        migrations.AlterField(
            model_name="confirmationemailtemplate",
            name="content_en",
            field=models.TextField(
                blank=True,
                help_text="The content of the email message can contain variables that will be templated from the submitted form data.",
                null=True,
                validators=[
                    openforms.template.validators.DjangoTemplateValidator(
                        backend="openforms.template.openforms_backend",
                        required_template_tags=[
                            "appointment_information",
                            "payment_information",
                            "cosign_information",
                        ],
                    ),
                    openforms.emails.validators.URLSanitationValidator(),
                ],
                verbose_name="content",
            ),
        ),
        migrations.AlterField(
            model_name="confirmationemailtemplate",
            name="content_nl",
            field=models.TextField(
                blank=True,
                help_text="The content of the email message can contain variables that will be templated from the submitted form data.",
                null=True,
                validators=[
                    openforms.template.validators.DjangoTemplateValidator(
                        backend="openforms.template.openforms_backend",
                        required_template_tags=[
                            "appointment_information",
                            "payment_information",
                            "cosign_information",
                        ],
                    ),
                    openforms.emails.validators.URLSanitationValidator(),
                ],
                verbose_name="content",
            ),
        ),
    ]
