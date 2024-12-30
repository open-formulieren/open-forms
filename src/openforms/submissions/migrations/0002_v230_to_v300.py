# Generated by Django 4.2.17 on 2024-12-27 16:04

import re

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models

import django_jsonform.models.fields

import openforms.submissions.models.email_verification
import openforms.submissions.models.submission_value_variable


class Migration(migrations.Migration):

    replaces = [
        ("submissions", "0002_change_json_encoder"),
        ("submissions", "0003_cleanup_urls"),
        ("submissions", "0004_auto_20231128_1536"),
        ("submissions", "0005_temporaryfileupload_legacy_and_more"),
        ("submissions", "0006_set_legacy_true"),
        ("submissions", "0007_add_legacy_constraint"),
        ("submissions", "0008_submission_initial_data_reference"),
        (
            "submissions",
            "0009_submission_only_completed_submission_has_finalised_registration_backend_key",
        ),
        ("submissions", "0010_emailverification"),
        ("submissions", "0011_remove_submissionstep__data"),
        ("submissions", "0012_alter_submission_price"),
        (
            "submissions",
            "0013_remove_temporaryfileupload_non_legacy_submission_not_null_and_more",
        ),
        ("submissions", "0013_remove_submission_previous_submission"),
        ("submissions", "0014_merge_20241211_1732"),
    ]

    dependencies = [
        ("submissions", "0001_initial_to_openforms_v230"),
    ]

    operations = [
        migrations.AlterField(
            model_name="submissionvaluevariable",
            name="value",
            field=models.JSONField(
                blank=True,
                encoder=openforms.submissions.models.submission_value_variable.ValueEncoder,
                help_text="The value of the variable",
                null=True,
                verbose_name="value",
            ),
        ),
        migrations.AddField(
            model_name="submission",
            name="cosign_confirmation_email_sent",
            field=models.BooleanField(
                default=False,
                help_text="Has the confirmation email been sent after the submission has successfully been cosigned?",
                verbose_name="cosign confirmation email sent",
            ),
        ),
        migrations.AddField(
            model_name="submission",
            name="cosign_request_email_sent",
            field=models.BooleanField(
                default=False,
                help_text="Has the email to request a co-sign been sent?",
                verbose_name="cosign request email sent",
            ),
        ),
        migrations.AddField(
            model_name="submission",
            name="payment_complete_confirmation_email_sent",
            field=models.BooleanField(
                default=False,
                help_text="Has the confirmation emails been sent after successful payment?",
                verbose_name="payment complete confirmation email sent",
            ),
        ),
        migrations.CreateModel(
            name="PostCompletionMetadata",
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
                    "tasks_ids",
                    django_jsonform.models.fields.ArrayField(
                        base_field=models.CharField(
                            blank=True, max_length=255, verbose_name="celery task ID"
                        ),
                        blank=True,
                        default=list,
                        help_text="Celery task IDs of the tasks queued once a post submission event happens.",
                        size=None,
                        verbose_name="task IDs",
                    ),
                ),
                (
                    "created_on",
                    models.DateTimeField(auto_now_add=True, verbose_name="created on"),
                ),
                (
                    "trigger_event",
                    models.CharField(
                        choices=[
                            ("on_completion", "On completion"),
                            ("on_payment_complete", "On payment complete"),
                            ("on_cosign_complete", "On cosign complete"),
                            ("on_retry", "On retry"),
                        ],
                        help_text="Which event scheduled these tasks.",
                        max_length=100,
                        verbose_name="created by",
                    ),
                ),
                (
                    "submission",
                    models.ForeignKey(
                        help_text="Submission to which the result belongs to.",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="submissions.submission",
                        verbose_name="submission",
                    ),
                ),
            ],
            options={
                "verbose_name": "post completion metadata",
                "verbose_name_plural": "post completion metadata",
            },
        ),
        migrations.AddConstraint(
            model_name="postcompletionmetadata",
            constraint=models.UniqueConstraint(
                condition=models.Q(("trigger_event", "on_completion")),
                fields=("submission",),
                name="unique_on_completion_event",
            ),
        ),
        migrations.AddField(
            model_name="temporaryfileupload",
            name="submission",
            field=models.ForeignKey(
                help_text="Submission the temporary file upload belongs to.",
                on_delete=django.db.models.deletion.CASCADE,
                to="submissions.submission",
                verbose_name="submission",
            ),
        ),
        migrations.AddField(
            model_name="submission",
            name="initial_data_reference",
            field=models.CharField(
                blank=True,
                help_text="An identifier that can be passed as a querystring when the form is started. Initial form field values are pre-populated from the retrieved data. During registration, the object may be updated again (or a new record may be created). This can be an object reference in the Objects API, for example.",
                verbose_name="initial data reference",
            ),
        ),
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
        migrations.CreateModel(
            name="EmailVerification",
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
                    "component_key",
                    models.TextField(
                        help_text="Key of the email component in the submission's form.",
                        validators=[
                            django.core.validators.RegexValidator(
                                message="Invalid variable key. It must only contain alphanumeric characters, underscores, dots and dashes and should not be ended by dash or dot.",
                                regex=re.compile("^(\\w|\\w[\\w.\\-]*\\w)$"),
                            )
                        ],
                        verbose_name="component key",
                    ),
                ),
                (
                    "email",
                    models.EmailField(
                        help_text="The email address that is being verified.",
                        max_length=254,
                        verbose_name="email address",
                    ),
                ),
                (
                    "verification_code",
                    models.CharField(
                        default=openforms.submissions.models.email_verification.generate_verification_code,
                        max_length=6,
                        verbose_name="verification code",
                    ),
                ),
                (
                    "verified_on",
                    models.DateTimeField(
                        blank=True,
                        help_text="Unverified emails have no timestamp set.",
                        null=True,
                        verbose_name="verification timestamp",
                    ),
                ),
                (
                    "submission",
                    models.ForeignKey(
                        help_text="The submission during which the email verification was initiated.",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="submissions.submission",
                        verbose_name="submission",
                    ),
                ),
            ],
            options={
                "verbose_name": "email verification",
                "verbose_name_plural": "email verifications",
            },
        ),
        migrations.RemoveField(
            model_name="submissionstep",
            name="_data",
        ),
        migrations.AlterField(
            model_name="submission",
            name="price",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                editable=False,
                help_text="Cost of this submission. Either derived from the related product, or set through logic rules. The price is calculated and saved on submission completion.",
                max_digits=10,
                null=True,
                verbose_name="price",
            ),
        ),
        migrations.RemoveField(
            model_name="submission",
            name="previous_submission",
        ),
    ]