# Generated by Django 3.2.15 on 2022-09-16 14:45

import uuid

import django.contrib.postgres.fields.jsonb
import django.db.migrations.operations.special
import django.db.models.deletion
from django.db import migrations, models

import django_better_admin_arrayfield.models.fields
import privates.fields
import privates.storages

import openforms.contrib.kvk.validators
import openforms.submissions.models.submission
import openforms.submissions.models.submission_files
import openforms.submissions.serializers
import openforms.utils.fields
import openforms.utils.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("forms", "0015_merge_20210514_1410"),
        ("forms", "0025_formvariable_valid_prefill_configuration"),
        ("forms", "0005_form_product"),
        ("forms", "0002_delete_formsubmission"),
        ("config", "0008_globalconfiguration_default_test_kvk"),
    ]

    operations = [
        migrations.CreateModel(
            name="Submission",
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
                    "uuid",
                    models.UUIDField(
                        default=uuid.uuid4, unique=True, verbose_name="UUID"
                    ),
                ),
                (
                    "form",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, to="forms.form"
                    ),
                ),
                (
                    "form_url",
                    models.URLField(
                        default="",
                        help_text="URL where the user initialized the submission.",
                        max_length=255,
                        validators=[
                            openforms.utils.validators.AllowedRedirectValidator()
                        ],
                        verbose_name="form URL",
                    ),
                ),
                (
                    "created_on",
                    models.DateTimeField(auto_now_add=True, verbose_name="created on"),
                ),
                (
                    "completed_on",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="completed on"
                    ),
                ),
                (
                    "suspended_on",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="suspended on"
                    ),
                ),
                (
                    "co_sign_data",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Authentication details of a co-signer.",
                        validators=[
                            openforms.utils.validators.SerializerValidator(
                                openforms.submissions.serializers.CoSignDataSerializer
                            )
                        ],
                        verbose_name="co-sign data",
                    ),
                ),
                (
                    "price",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        editable=False,
                        help_text="Cost of this submission. Either derived from the related product, or evaluated from price logic rules. The price is calculated and saved on submission completion.",
                        max_digits=10,
                        null=True,
                        verbose_name="price",
                    ),
                ),
                (
                    "auth_plugin",
                    models.CharField(
                        blank=True,
                        help_text="The plugin used by the user for authentication.",
                        max_length=100,
                        verbose_name="auth plugin",
                    ),
                ),
                (
                    "last_register_date",
                    models.DateTimeField(
                        blank=True,
                        help_text="The last time the submission registration was attempted with the backend.  Note that this date will be updated even if the registration is not successful.",
                        null=True,
                        verbose_name="last register attempt date",
                    ),
                ),
                (
                    "registration_attempts",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Counter to track how often we tried calling the registration backend. ",
                        verbose_name="registration backend retry counter",
                    ),
                ),
                (
                    "registration_result",
                    models.JSONField(
                        blank=True,
                        help_text="Contains data returned by the registration backend while registering the submission data.",
                        null=True,
                        verbose_name="registration backend result",
                    ),
                ),
                (
                    "registration_status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending (not registered yet)"),
                            ("in_progress", "In progress (not registered yet)"),
                            ("success", "Success"),
                            ("failed", "Failed"),
                        ],
                        default="pending",
                        help_text="Indication whether the registration in the configured backend was successful.",
                        max_length=50,
                        verbose_name="registration backend status",
                    ),
                ),
                (
                    "public_registration_reference",
                    models.CharField(
                        blank=True,
                        help_text="The registration reference communicated to the end-user completing the form. This reference is intended to be unique and the reference the end-user uses to communicate with the service desk. It should be extracted from the registration result where possible, and otherwise generated to be unique. Note that this reference is displayed to the end-user and used as payment reference!",
                        max_length=100,
                        verbose_name="public registration reference",
                    ),
                ),
                (
                    "confirmation_email_sent",
                    models.BooleanField(
                        default=False,
                        help_text="Indicates whether the confirmation email has been sent.",
                        verbose_name="confirmation email sent",
                    ),
                ),
                (
                    "bsn",
                    models.CharField(
                        blank=True,
                        default=openforms.submissions.models.submission.get_default_bsn,
                        max_length=255,
                        validators=[openforms.utils.validators.BSNValidator()],
                        verbose_name="BSN",
                    ),
                ),
                (
                    "kvk",
                    models.CharField(
                        blank=True,
                        default=openforms.submissions.models.submission.get_default_kvk,
                        max_length=255,
                        validators=[
                            openforms.contrib.kvk.validators.KVKNumberValidator()
                        ],
                        verbose_name="KvK number",
                    ),
                ),
                (
                    "pseudo",
                    models.CharField(
                        blank=True,
                        help_text="Pseudo ID provided by authentication with eIDAS",
                        max_length=255,
                        verbose_name="Pseudo ID",
                    ),
                ),
                (
                    "auth_attributes_hashed",
                    models.BooleanField(
                        default=False,
                        editable=False,
                        help_text="are the auth/identifying attributes hashed?",
                        verbose_name="identifying attributes hashed",
                    ),
                ),
                (
                    "_is_cleaned",
                    models.BooleanField(
                        default=False,
                        help_text="Indicates whether sensitive data (if there was any) has been removed from this submission.",
                        verbose_name="is cleaned",
                    ),
                ),
                (
                    "on_completion_task_ids",
                    django_better_admin_arrayfield.models.fields.ArrayField(
                        base_field=models.CharField(
                            blank=True,
                            max_length=255,
                            verbose_name="on completion task ID",
                        ),
                        blank=True,
                        default=list,
                        help_text="Celery task IDs of the on_completion workflow. Use this to inspect the state of the async jobs.",
                        size=None,
                        verbose_name="on completion task IDs",
                    ),
                ),
                (
                    "needs_on_completion_retry",
                    models.BooleanField(
                        default=False,
                        help_text="Flag to track if the on_completion_retry chain should be invoked. This is scheduled via celery-beat.",
                        verbose_name="needs on_completion retry",
                    ),
                ),
            ],
            options={
                "verbose_name": "submission",
                "verbose_name_plural": "submissions",
            },
        ),
        migrations.AddConstraint(
            model_name="submission",
            constraint=models.UniqueConstraint(
                condition=models.Q(
                    ("public_registration_reference", ""), _negated=True
                ),
                fields=("public_registration_reference",),
                name="unique_public_registration_reference",
            ),
        ),
        migrations.AddField(
            model_name="submission",
            name="previous_submission",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="submissions.submission",
            ),
        ),
        migrations.CreateModel(
            name="SubmissionStep",
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
                    "uuid",
                    models.UUIDField(
                        default=uuid.uuid4, unique=True, verbose_name="UUID"
                    ),
                ),
                (
                    "data",
                    django.contrib.postgres.fields.jsonb.JSONField(
                        blank=True, null=True, verbose_name="data"
                    ),
                ),
                (
                    "created_on",
                    models.DateTimeField(auto_now_add=True, verbose_name="created on"),
                ),
                (
                    "form_step",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="forms.formstep"
                    ),
                ),
                (
                    "submission",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="submissions.submission",
                    ),
                ),
                (
                    "modified",
                    models.DateTimeField(auto_now=True, verbose_name="modified on"),
                ),
            ],
            options={
                "verbose_name": "Submission step",
                "verbose_name_plural": "Submission steps",
                "unique_together": {("submission", "form_step")},
            },
        ),
        migrations.CreateModel(
            name="SubmissionReport",
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
                    "title",
                    models.CharField(
                        help_text="Title of the submission report",
                        max_length=200,
                        verbose_name="title",
                    ),
                ),
                (
                    "content",
                    privates.fields.PrivateMediaFileField(
                        help_text="Content of the submission report",
                        storage=privates.storages.PrivateMediaFileSystemStorage(),
                        upload_to="submission-reports/%Y/%m/%d",
                        verbose_name="content",
                    ),
                ),
                (
                    "last_accessed",
                    models.DateTimeField(
                        blank=True,
                        help_text="When the submission report was last accessed. This value is updated when the report is downloaded.",
                        null=True,
                        verbose_name="last accessed",
                    ),
                ),
                (
                    "submission",
                    models.OneToOneField(
                        blank=True,
                        help_text="Submission the report is about.",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="report",
                        to="submissions.submission",
                        verbose_name="submission",
                    ),
                ),
                (
                    "task_id",
                    models.CharField(
                        blank=True,
                        help_text="ID of the celery task creating the content of the report. This is used to check the generation status.",
                        max_length=200,
                        verbose_name="task id",
                    ),
                ),
            ],
            options={
                "verbose_name": "submission report",
                "verbose_name_plural": "submission reports",
            },
        ),
        migrations.CreateModel(
            name="TemporaryFileUpload",
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
                    "uuid",
                    models.UUIDField(
                        default=uuid.uuid4, unique=True, verbose_name="UUID"
                    ),
                ),
                (
                    "content",
                    privates.fields.PrivateMediaFileField(
                        help_text="content of the file attachment.",
                        storage=privates.storages.PrivateMediaFileSystemStorage(),
                        upload_to=openforms.submissions.models.submission_files.temporary_file_upload_to,
                        verbose_name="content",
                    ),
                ),
                (
                    "file_name",
                    models.CharField(max_length=255, verbose_name="original name"),
                ),
                (
                    "file_size",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Size in bytes of the uploaded file.",
                        verbose_name="file size",
                    ),
                ),
                (
                    "content_type",
                    models.CharField(max_length=255, verbose_name="content type"),
                ),
                (
                    "created_on",
                    models.DateTimeField(auto_now_add=True, verbose_name="created on"),
                ),
            ],
            options={
                "verbose_name": "temporary file upload",
                "verbose_name_plural": "temporary file uploads",
            },
        ),
        migrations.CreateModel(
            name="SubmissionFileAttachment",
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
                    "uuid",
                    models.UUIDField(
                        default=uuid.uuid4, unique=True, verbose_name="UUID"
                    ),
                ),
                (
                    "form_key",
                    models.CharField(max_length=255, verbose_name="form component key"),
                ),
                (
                    "content",
                    privates.fields.PrivateMediaFileField(
                        help_text="Content of the submission file attachment.",
                        storage=privates.storages.PrivateMediaFileSystemStorage(),
                        upload_to=openforms.submissions.models.submission_files.submission_file_upload_to,
                        verbose_name="content",
                    ),
                ),
                (
                    "file_name",
                    models.CharField(
                        blank=True,
                        help_text="reformatted file name",
                        max_length=255,
                        verbose_name="file name",
                    ),
                ),
                (
                    "original_name",
                    models.CharField(
                        help_text="original uploaded file name",
                        max_length=255,
                        verbose_name="original name",
                    ),
                ),
                (
                    "content_type",
                    models.CharField(max_length=255, verbose_name="content type"),
                ),
                (
                    "created_on",
                    models.DateTimeField(auto_now_add=True, verbose_name="created on"),
                ),
                (
                    "submission_step",
                    models.ForeignKey(
                        help_text="Submission step the file is attached to.",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attachments",
                        to="submissions.submissionstep",
                        verbose_name="submission",
                    ),
                ),
                (
                    "temporary_file",
                    models.ForeignKey(
                        help_text="Temporary upload this file is sourced to.",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="attachments",
                        to="submissions.temporaryfileupload",
                        verbose_name="temporary file",
                    ),
                ),
            ],
            options={
                "base_manager_name": "objects",
                "verbose_name": "submission file attachment",
                "verbose_name_plural": "submission file attachments",
            },
        ),
        migrations.AddField(
            model_name="submission",
            name="prefill_data",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text="Data used for prefills.",
                verbose_name="prefill data",
            ),
        ),
        migrations.CreateModel(
            name="SubmissionValueVariable",
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
                    "key",
                    models.TextField(
                        help_text="Key of the variable", verbose_name="key"
                    ),
                ),
                (
                    "value",
                    models.JSONField(
                        blank=True,
                        help_text="The value of the variable",
                        null=True,
                        verbose_name="value",
                    ),
                ),
                (
                    "source",
                    models.CharField(
                        choices=[
                            ("static", "Static"),
                            ("sensitive_data_cleaner", "Sensitive data cleaner"),
                            ("user_input", "User input"),
                            ("prefill", "Prefill"),
                            ("logic", "Logic"),
                            ("dmn", "DMN"),
                        ],
                        help_text="Where variable value came from",
                        max_length=50,
                        verbose_name="source",
                    ),
                ),
                (
                    "language",
                    models.CharField(
                        blank=True,
                        help_text="If this value contains text, in which language is it?",
                        max_length=50,
                        verbose_name="language",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="The date/time at which the value of this variable was created",
                        verbose_name="created at",
                    ),
                ),
                (
                    "modified_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="The date/time at which the value of this variable was last set",
                        null=True,
                        verbose_name="modified at",
                    ),
                ),
                (
                    "form_variable",
                    models.ForeignKey(
                        help_text="The form variable to which this value is related",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="forms.formvariable",
                        verbose_name="form variable",
                    ),
                ),
                (
                    "submission",
                    models.ForeignKey(
                        help_text="The submission to which this variable value is related",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="submissions.submission",
                        verbose_name="submission",
                    ),
                ),
            ],
            options={
                "verbose_name": "Submission value variable",
                "verbose_name_plural": "Submission values variables",
                "unique_together": {
                    ("submission", "key"),
                    ("submission", "form_variable"),
                },
            },
        ),
        migrations.RenameField(
            model_name="submissionstep",
            old_name="data",
            new_name="_data",
        ),
        migrations.AlterField(
            model_name="submissionstep",
            name="_data",
            field=models.JSONField(blank=True, null=True, verbose_name="data"),
        ),
        migrations.AddField(
            model_name="submissionfileattachment",
            name="submission_variable",
            field=models.ForeignKey(
                blank=True,
                help_text="submission value variable for the form component",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="submissions.submissionvaluevariable",
                verbose_name="submission variable",
            ),
        ),
    ]
