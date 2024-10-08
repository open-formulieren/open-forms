# Generated by Django 4.2.11 on 2024-07-04 10:53

import functools

from django.db import migrations, models

import tinymce.models
from flags.conditions import boolean_condition

import openforms.config.models.config
import openforms.emails.validators
import openforms.payments.validators
import openforms.template.validators

FIELDS = (
    "enable_demo_plugins",
    "display_sdk_information",
)


def move_from_config_to_flagstate(apps, _):
    GlobalConfiguration = apps.get_model("config", "GlobalConfiguration")
    FlagState = apps.get_model("flags", "FlagState")

    # ensure we have an instance, for a fresh install, this will set up the
    # defaults explicitly.
    config = GlobalConfiguration.objects.first() or GlobalConfiguration()
    for field in FIELDS:
        current_value = getattr(config, field)
        FlagState.objects.get_or_create(
            name=field.upper(),
            defaults={
                "condition": "boolean",
                "value": str(current_value),
                "required": False,
            },
        )


def move_from_flagstate_to_config(apps, _):
    GlobalConfiguration = apps.get_model("config", "GlobalConfiguration")
    FlagState = apps.get_model("flags", "FlagState")

    # if there's no config, there's nothing to do
    config = GlobalConfiguration.objects.first()
    if config is None:
        return

    for field in FIELDS:
        flag_state = FlagState.objects.filter(
            name=field.upper(), condition="boolean"
        ).first()
        if flag_state is None:
            continue

        value = boolean_condition(flag_state.value)
        setattr(config, field, value)

    config.save()


class Migration(migrations.Migration):

    dependencies = [
        ("config", "0001_initial_to_v250"),
        ("upgrades", "0001_initial"),
        ("flags", "0013_add_required_field"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="globalconfiguration",
            name="enable_react_formio_builder",
        ),
        migrations.AddField(
            model_name="globalconfiguration",
            name="payment_order_id_template",
            field=models.CharField(
                default="{year}/{public_reference}/{uid}",
                help_text="Template to use when generating payment order IDs. It should be alpha-numerical and can contain the '/._-' characters. You can use the placeholder tokens: {year}, {public_reference}, {uid}.",
                max_length=48,
                validators=[
                    openforms.payments.validators.validate_payment_order_id_template
                ],
                verbose_name="Payment Order ID template",
            ),
        ),
        migrations.RemoveField(
            model_name="globalconfiguration",
            name="payment_order_id_prefix",
        ),
        migrations.AddField(
            model_name="theme",
            name="email_logo",
            field=models.ImageField(
                blank=True,
                help_text="Upload the email logo, visible to users who receive an email. We advise dimensions around 150px by 75px. SVG's are not permitted.",
                upload_to="logo/",
                verbose_name="email logo",
            ),
        ),
        migrations.AddField(
            model_name="globalconfiguration",
            name="cosign_request_template",
            field=tinymce.models.HTMLField(
                default=functools.partial(
                    openforms.config.models.config._render,
                    *("emails/co_sign/request.html",),
                    **{}
                ),
                help_text="Content of the co-sign request email. The available template variables are: 'form_name', 'form_url' and 'code'.",
                validators=[
                    openforms.template.validators.DjangoTemplateValidator(
                        backend="openforms.template.openforms_backend"
                    ),
                    openforms.emails.validators.URLSanitationValidator(),
                ],
                verbose_name="co-sign request template",
            ),
        ),
        migrations.AddField(
            model_name="globalconfiguration",
            name="cosign_request_template_en",
            field=tinymce.models.HTMLField(
                default=functools.partial(
                    openforms.config.models.config._render,
                    *("emails/co_sign/request.html",),
                    **{}
                ),
                help_text="Content of the co-sign request email. The available template variables are: 'form_name', 'form_url' and 'code'.",
                null=True,
                validators=[
                    openforms.template.validators.DjangoTemplateValidator(
                        backend="openforms.template.openforms_backend"
                    ),
                    openforms.emails.validators.URLSanitationValidator(),
                ],
                verbose_name="co-sign request template",
            ),
        ),
        migrations.AddField(
            model_name="globalconfiguration",
            name="cosign_request_template_nl",
            field=tinymce.models.HTMLField(
                default=functools.partial(
                    openforms.config.models.config._render,
                    *("emails/co_sign/request.html",),
                    **{}
                ),
                help_text="Content of the co-sign request email. The available template variables are: 'form_name', 'form_url' and 'code'.",
                null=True,
                validators=[
                    openforms.template.validators.DjangoTemplateValidator(
                        backend="openforms.template.openforms_backend"
                    ),
                    openforms.emails.validators.URLSanitationValidator(),
                ],
                verbose_name="co-sign request template",
            ),
        ),
        migrations.RemoveField(
            model_name="globalconfiguration",
            name="show_form_link_in_cosign_email",
        ),
        migrations.RunPython(
            code=move_from_config_to_flagstate,
            reverse_code=move_from_flagstate_to_config,
        ),
        migrations.RemoveField(
            model_name="globalconfiguration",
            name="display_sdk_information",
        ),
        migrations.RemoveField(
            model_name="globalconfiguration",
            name="enable_demo_plugins",
        ),
    ]
