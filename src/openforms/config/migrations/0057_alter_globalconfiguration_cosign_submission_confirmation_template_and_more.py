# Generated by Django 4.2.18 on 2025-03-17 12:00

import functools

from django.db import migrations, models

import tinymce.models

import openforms.config.models.config
import openforms.template.validators
import openforms.utils.translations


class Migration(migrations.Migration):
    dependencies = [
        ("config", "0056_globalconfiguration_referentielijsten_services"),
    ]

    operations = [
        migrations.AlterField(
            model_name="globalconfiguration",
            name="cosign_submission_confirmation_template",
            field=tinymce.models.HTMLField(
                default=functools.partial(
                    openforms.config.models.config._render,
                    *("config/default_cosign_submission_confirmation.html",),
                    **{},
                ),
                help_text="The content of the submission confirmation page for submissions requiring cosigning. The variables 'public_reference' and 'cosigner_email' are available (using expressions '{{ public_reference }}' and '{{ cosigner_email }}', respectively). We strongly advise you to include the 'public_reference' in case users need to contact the customer service.",
                validators=[
                    openforms.template.validators.DjangoTemplateValidator(
                        backend="openforms.template.openforms_backend"
                    )
                ],
                verbose_name="cosign submission confirmation template",
            ),
        ),
        migrations.AlterField(
            model_name="globalconfiguration",
            name="cosign_submission_confirmation_template_en",
            field=tinymce.models.HTMLField(
                default=functools.partial(
                    openforms.config.models.config._render,
                    *("config/default_cosign_submission_confirmation.html",),
                    **{},
                ),
                help_text="The content of the submission confirmation page for submissions requiring cosigning. The variables 'public_reference' and 'cosigner_email' are available (using expressions '{{ public_reference }}' and '{{ cosigner_email }}', respectively). We strongly advise you to include the 'public_reference' in case users need to contact the customer service.",
                null=True,
                validators=[
                    openforms.template.validators.DjangoTemplateValidator(
                        backend="openforms.template.openforms_backend"
                    )
                ],
                verbose_name="cosign submission confirmation template",
            ),
        ),
        migrations.AlterField(
            model_name="globalconfiguration",
            name="cosign_submission_confirmation_template_nl",
            field=tinymce.models.HTMLField(
                default=functools.partial(
                    openforms.config.models.config._render,
                    *("config/default_cosign_submission_confirmation.html",),
                    **{},
                ),
                help_text="The content of the submission confirmation page for submissions requiring cosigning. The variables 'public_reference' and 'cosigner_email' are available (using expressions '{{ public_reference }}' and '{{ cosigner_email }}', respectively). We strongly advise you to include the 'public_reference' in case users need to contact the customer service.",
                null=True,
                validators=[
                    openforms.template.validators.DjangoTemplateValidator(
                        backend="openforms.template.openforms_backend"
                    )
                ],
                verbose_name="cosign submission confirmation template",
            ),
        ),
        migrations.AlterField(
            model_name="globalconfiguration",
            name="submission_confirmation_title",
            field=models.CharField(
                default=functools.partial(
                    openforms.utils.translations.get_default,
                    *("Confirmation: {{ public_reference }}",),
                    **{},
                ),
                help_text="The content of the confirmation page title. You can (and should) include the 'public_reference' variable (using expression '{{ public_reference }}') so the users have a reference in case they need to contact the customer service.",
                max_length=200,
                validators=[openforms.template.validators.DjangoTemplateValidator()],
                verbose_name="submission confirmation title",
            ),
        ),
        migrations.AlterField(
            model_name="globalconfiguration",
            name="submission_confirmation_title_en",
            field=models.CharField(
                default=functools.partial(
                    openforms.utils.translations.get_default,
                    *("Confirmation: {{ public_reference }}",),
                    **{},
                ),
                help_text="The content of the confirmation page title. You can (and should) include the 'public_reference' variable (using expression '{{ public_reference }}') so the users have a reference in case they need to contact the customer service.",
                max_length=200,
                null=True,
                validators=[openforms.template.validators.DjangoTemplateValidator()],
                verbose_name="submission confirmation title",
            ),
        ),
        migrations.AlterField(
            model_name="globalconfiguration",
            name="submission_confirmation_title_nl",
            field=models.CharField(
                default=functools.partial(
                    openforms.utils.translations.get_default,
                    *("Confirmation: {{ public_reference }}",),
                    **{},
                ),
                help_text="The content of the confirmation page title. You can (and should) include the 'public_reference' variable (using expression '{{ public_reference }}') so the users have a reference in case they need to contact the customer service.",
                max_length=200,
                null=True,
                validators=[openforms.template.validators.DjangoTemplateValidator()],
                verbose_name="submission confirmation title",
            ),
        ),
    ]
