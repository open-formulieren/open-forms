from datetime import timedelta

from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.contenttypes.admin import GenericTabularInline
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Q
from django.http import Http404
from django.template.defaultfilters import filesizeformat
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html_join
from django.utils.translation import gettext_lazy as _, ngettext

from privates.admin import PrivateMediaMixin
from privates.views import PrivateMediaView

from openforms.appointments.models import AppointmentInfo
from openforms.authentication.admin import AuthInfoInline
from openforms.forms.models import Form
from openforms.logging import audit_logger
from openforms.logging.constants import TimelineLogTags
from openforms.logging.models import TimelineLogProxy
from openforms.payments.models import SubmissionPayment
from openforms.typing import StrOrPromise, is_authenticated_request

from .constants import IMAGE_COMPONENTS, PostSubmissionEvents, RegistrationStatuses
from .exports import ExportFileTypes, export_submissions
from .models import (
    EmailVerification,
    Submission,
    SubmissionFileAttachment,
    SubmissionReport,
    SubmissionStep,
    SubmissionValueVariable,
    TemporaryFileUpload,
)
from .pricing import InvalidPrice
from .tasks import on_post_submission_event


class SubmissionTypeListFilter(admin.ListFilter):
    title = _("type")
    parameter_name = "type"

    def __init__(self, request, params, model, model_admin):
        super().__init__(request, params, model, model_admin)

        self.request = request

        if self.parameter_name in params:
            value = params.pop(self.parameter_name)
            self.used_parameters[self.parameter_name] = value[-1]

    def show_all(self):
        return self.used_parameters.get(self.parameter_name) == "__all__"

    def has_output(self):
        """
        This needs to return ``True`` to work.
        """
        return True

    def choices(self, changelist):
        result = [
            {
                "selected": self.show_all(),
                "query_string": changelist.get_query_string(
                    {self.parameter_name: "__all__"}
                ),
                "display": _("All"),
            },
            {
                "selected": not self.show_all(),
                "query_string": changelist.get_query_string(
                    remove=[self.parameter_name]
                ),
                "display": _("Submissions"),
            },
        ]
        return result

    def queryset(self, request, queryset):
        if not self.show_all():
            return queryset.exclude(completed_on=None)

    def expected_parameters(self):
        return [self.parameter_name]


class SubmissionTimeListFilter(admin.SimpleListFilter):
    title = _("registration time")
    parameter_name = "registration_time"

    def lookups(self, request, model_admin):
        return [
            ("24hAgo", _("In the past 24 hours")),
        ]

    def queryset(self, request, queryset):
        yesterday = timezone.now() - timedelta(days=1)
        if self.value() == "24hAgo":
            return queryset.filter(last_register_date__gt=yesterday)


class SubmissionStepInline(admin.TabularInline):
    model = SubmissionStep
    extra = 0
    fields = ("uuid", "form_step", "created_on", "modified")
    raw_id_fields = ("form_step",)
    readonly_fields = ("created_on", "modified")


class SubmissionPaymentInline(admin.StackedInline):
    model = SubmissionPayment
    extra = 0
    fields = (
        "uuid",
        "created",
        "submission",
        "plugin_id",
        "public_order_id",
        "amount",
        "status",
    )
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class SubmissionLogInline(GenericTabularInline):
    model = TimelineLogProxy
    fields = ("get_message",)
    readonly_fields = ("get_message",)
    template = "logging/admin_inline.html"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.has_tag(TimelineLogTags.submission_lifecycle)
        qs = qs.filter(~Q(template="logging/events/submission_logic_evaluated.txt"))
        return qs.prefetch_related(
            "content_object", "content_object__form"
        ).select_related("user")

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class SubmissionValueVariableAdminForm(forms.ModelForm):
    class Meta:
        model = SubmissionValueVariable
        fields = ("key", "value", "source")
        widgets = {
            "value": forms.Textarea(attrs={"cols": 40, "rows": 1}),
        }


class SubmissionValueVariableInline(admin.TabularInline):
    model = SubmissionValueVariable

    fields = ("key", "value", "source")
    readonly_fields = ("key", "source")
    extra = 0
    form = SubmissionValueVariableAdminForm


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    date_hierarchy = "completed_on"
    list_display = (
        "form",
        "public_registration_reference",
        "registration_status",
        "last_register_date",
        "successfully_processed",
        "created_on",
        "completed_on",
    )
    list_filter = (
        SubmissionTypeListFilter,
        SubmissionTimeListFilter,
        "registration_status",
        "needs_on_completion_retry",
        "form",
    )
    ordering = ("-pk",)
    search_fields = (
        "uuid",
        "form__name",
        "form__internal_name",
        "form__slug",
        "form_url",
        "public_registration_reference",
    )
    inlines = [
        SubmissionStepInline,
        AuthInfoInline,
        SubmissionValueVariableInline,
        SubmissionPaymentInline,
        SubmissionLogInline,
    ]
    readonly_fields = [
        "created_on",
        "co_sign_data",
        "get_registration_backend",
        "get_appointment_status",
        "get_appointment_id",
        "get_appointment_error_information",
        "post_completion_task_ids",
        "confirmation_email_sent",
        "registration_attempts",
        "pre_registration_completed",
        "cosign_complete",
        "cosign_request_email_sent",
        "cosign_confirmation_email_sent",
        "cosign_privacy_policy_accepted",
        "privacy_policy_accepted",
        "statement_of_truth_accepted",
        "cosign_statement_of_truth_accepted",
        "payment_complete_confirmation_email_sent",
        "get_price",
        "get_payment_required",
    ]
    fieldsets = (
        (
            _("Metadata"),
            {
                "fields": (
                    "public_registration_reference",
                    "uuid",
                    "form",
                    "form_url",
                    "language_code",
                )
            },
        ),
        (
            _("Important dates"),
            {
                "fields": (
                    "created_on",
                    "completed_on",
                    "suspended_on",
                )
            },
        ),
        (
            _("Registration"),
            {
                "fields": (
                    "get_registration_backend",
                    "registration_status",
                    "last_register_date",
                    "registration_attempts",
                    "finalised_registration_backend_key",
                    "pre_registration_completed",
                    "registration_result",
                )
            },
        ),
        (
            _("Appointment"),
            {
                "fields": (
                    "get_appointment_status",
                    "get_appointment_id",
                    "get_appointment_error_information",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Co-sign"),
            {
                "fields": (
                    "cosign_complete",
                    "cosign_request_email_sent",
                    "co_sign_data",
                    "cosign_confirmation_email_sent",
                    "cosign_privacy_policy_accepted",
                    "cosign_statement_of_truth_accepted",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Payment"),
            {
                "fields": (
                    "get_price",
                    "get_payment_required",
                    "payment_complete_confirmation_email_sent",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Background tasks"),
            {
                "fields": (
                    "post_completion_task_ids",
                    "needs_on_completion_retry",
                    "confirmation_email_sent",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Misc"),
            {
                "fields": (
                    "privacy_policy_accepted",
                    "statement_of_truth_accepted",
                    "_is_cleaned",
                    "initial_data_reference",
                ),
                "classes": ("collapse",),
            },
        ),
    )
    raw_id_fields = ("form",)
    actions = [
        "export_csv",
        "export_json",
        "export_xlsx",
        "export_xml",
        "retry_processing_submissions",
    ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.select_related("form")
        return qs

    def get_list_display(self, request):
        list_display = super().get_list_display(request)
        assert isinstance(list_display, tuple)
        if settings.DEBUG:
            list_display += ("dev_debug",)
        return list_display

    @admin.display(description=_("Successfully processed"), boolean=True)
    def successfully_processed(self, obj) -> bool | None:
        if obj.registration_status == RegistrationStatuses.pending:
            return None
        return not obj.needs_on_completion_retry

    @admin.display(description=_("Registration backend"))
    def get_registration_backend(self, obj: Submission):
        return obj.resolve_registration_backend(enable_log=False) or "-"

    @admin.display(description=_("Appointment status"))
    def get_appointment_status(self, obj):
        try:
            return obj.appointment_info.status
        except AppointmentInfo.DoesNotExist:
            return ""

    @admin.display(description=_("Appointment Id"))
    def get_appointment_id(self, obj):
        try:
            return obj.appointment_info.appointment_id
        except AppointmentInfo.DoesNotExist:
            return ""

    @admin.display(description=_("Appointment error information"))
    def get_appointment_error_information(self, obj):
        try:
            return obj.appointment_info.error_information
        except AppointmentInfo.DoesNotExist:
            return ""

    @admin.display(description=_("Price"), ordering="price")
    def get_price(self, obj):
        return obj.price or "-"

    @admin.display(description=_("Payment required"), boolean=True)
    def get_payment_required(self, obj):
        obj._in_admin_display = True
        try:
            return obj.payment_required
        # InvalidPrice means that pricing/payment was set up and configured, but a
        # semi-expected crash happened when trying to calculate the price because of
        # mis-configuration.
        except InvalidPrice:
            return True

    @admin.display(description="DEV/DEBUG")
    def dev_debug(self, obj: Submission):  # pragma: no cover
        if not settings.DEBUG:
            raise ImproperlyConfigured("Development-only admin feature!")

        links: list[tuple[str, StrOrPromise]] = [
            (
                reverse("dev-email-confirm", kwargs={"submission_id": obj.pk}),
                _("Confirmation email preview"),
            ),
            (
                reverse("dev-submissions-pdf", kwargs={"pk": obj.pk}),
                _("Submission PDF preview"),
            ),
            (
                reverse("dev-email-registration", kwargs={"submission_id": obj.pk}),
                _("Registration: email plugin preview"),
            ),
        ]
        return format_html_join(" | ", '<a href="{}" target="_blank">{}</a>', links)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        assert is_authenticated_request(request)
        submission = self.get_object(request, object_id)
        if submission is None:
            raise Http404(f"No {self.model._meta.object_name} matches the given query.")
        audit_logger.info(
            "submission_details_view_admin",
            submission_uuid=str(submission.uuid),
            user=request.user.username,
        )
        extra_context = {
            "attachments": submission.get_merged_attachments(),
            "image_components": IMAGE_COMPONENTS,
        }
        return super().change_view(
            request,
            object_id,
            form_url=form_url,
            extra_context=extra_context,
        )

    def _export(self, request, queryset, file_type):
        if queryset.order_by().values("form").distinct().count() > 1:
            messages.error(
                request,
                _("You can only export the submissions of the same form type."),
            )
            return

        form: Form = queryset[0].form
        audit_logger.info(
            "submission_export_list", form_id=form.pk, user=request.user.username
        )
        return export_submissions(queryset, file_type)

    @admin.action(description=_("Export selected %(verbose_name_plural)s as CSV-file."))
    def export_csv(self, request, queryset):
        return self._export(request, queryset, ExportFileTypes.CSV)

    @admin.action(
        description=_("Export selected %(verbose_name_plural)s as Excel-file.")
    )
    def export_xlsx(self, request, queryset):
        return self._export(request, queryset, ExportFileTypes.XLSX)

    @admin.action(
        description=_("Export selected %(verbose_name_plural)s as JSON-file.")
    )
    def export_json(self, request, queryset):
        return self._export(request, queryset, ExportFileTypes.JSON)

    @admin.action(description=_("Export selected %(verbose_name_plural)s as XML-file."))
    def export_xml(self, request, queryset):
        return self._export(request, queryset, ExportFileTypes.XML)

    @admin.action(description=_("Retry processing %(verbose_name_plural)s."))
    def retry_processing_submissions(self, request, queryset):
        submissions = queryset.filter(registration_status=RegistrationStatuses.failed)
        messages.success(
            request,
            ngettext(
                "Retrying processing flow for {count} {verbose_name} object",
                "Retrying processing flow for {count} {verbose_name} objects",
                submissions.count(),
            ).format(
                count=submissions.count(),
                verbose_name=queryset.model._meta.verbose_name,
                verbose_name_plural=queryset.model._meta.verbose_name_plural,
            ),
        )
        # reset attempts when manually retrying
        submissions.update(registration_attempts=0)

        for submission in submissions:
            on_post_submission_event(submission.id, PostSubmissionEvents.on_retry)


@admin.register(SubmissionReport)
class SubmissionReportAdmin(PrivateMediaMixin, admin.ModelAdmin):
    list_display = ("title",)
    list_filter = ("title",)
    search_fields = (
        "title",
        "submission__uuid",
        "submission__public_registration_reference",
    )
    raw_id_fields = ("submission",)

    private_media_fields = ("content",)
    private_media_view_options = {"attachment": True}
    readonly_fields = ("content",)

    def has_add_permission(self, request, obj=None):
        return False


class TemporaryFileUploadMediaView(PrivateMediaView):
    def get_sendfile_opts(self):
        object = self.get_object()
        return {
            "attachment": True,
            "attachment_filename": object.file_name,
            "mimetype": object.content_type,
        }


@admin.register(TemporaryFileUpload)
class TemporaryFileUploadAdmin(PrivateMediaMixin, admin.ModelAdmin):
    list_display = (
        "uuid",
        "file_name",
        "content_type",
        "created_on",
        "file_size",
    )
    fields = (
        "uuid",
        "created_on",
        "file_name",
        "content_type",
        "file_size",
        "content",
    )

    search_fields = ("uuid",)
    readonly_fields = (
        "uuid",
        "created_on",
        "file_name",
        "content_type",
        "file_size",
        "content",
    )
    date_hierarchy = "created_on"

    private_media_fields = ("content",)
    private_media_view_class = TemporaryFileUploadMediaView

    def file_size(self, obj):
        return filesizeformat(obj.content.size)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    file_size.short_description = _("File size")


class SubmissionFileAttachmentMediaView(PrivateMediaView):
    def get_sendfile_opts(self):
        object = self.get_object()
        return {
            "attachment": True,
            "attachment_filename": object.get_display_name(),
            "mimetype": object.content_type,
        }


@admin.register(SubmissionFileAttachment)
class SubmissionFileAttachmentAdmin(PrivateMediaMixin, admin.ModelAdmin):
    list_display = (
        "uuid",
        "get_display_name",
        "content_type",
        "created_on",
        "file_size",
    )
    fields = (
        "uuid",
        "submission_step",
        "submission_variable",
        "form_key_display",
        "created_on",
        "original_name",
        "get_display_name",
        "content_type",
        "file_size",
        "content",
    )
    raw_id_fields = (
        "submission_step",
        "submission_variable",
    )
    readonly_fields = (
        "uuid",
        "get_display_name",
        "created_on",
        "file_size",
        "form_key_display",
    )
    date_hierarchy = "created_on"

    private_media_fields = ("content",)
    private_media_view_class = SubmissionFileAttachmentMediaView

    def file_size(self, obj):
        return filesizeformat(obj.content.size)

    file_size.short_description = _("File size")

    def form_key_display(self, obj):
        if obj.submission_variable:
            return obj.submission_variable.key
        else:
            # this shouldn't happen but the field is nullable
            return "<legacy>"

    form_key_display.short_description = _("Form key")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ("email", "submission", "component_key", "is_verified")
    search_fields = (
        "email",
        "component_key",
        "submission__uuid",
        "submission__public_registration_reference",
    )
    readonly_fields = (
        "submission",
        "component_key",
    )

    @admin.display(description=_("is verified"), boolean=True)
    def is_verified(self, obj: EmailVerification) -> bool:
        return obj.verified_on is not None
