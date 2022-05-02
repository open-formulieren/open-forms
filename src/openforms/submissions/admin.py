from typing import Optional

from django.contrib import admin, messages
from django.contrib.contenttypes.admin import GenericTabularInline
from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext_lazy as _, ngettext

from privates.admin import PrivateMediaMixin
from privates.views import PrivateMediaView

from openforms.appointments.models import AppointmentInfo
from openforms.logging.constants import TimelineLogTags
from openforms.logging.logevent import (
    submission_details_view_admin,
    submission_export_list as log_export_submissions,
)
from openforms.logging.models import TimelineLogProxy
from openforms.payments.models import SubmissionPayment

from ..utils.admin import ReadOnlyAdminMixin
from .constants import IMAGE_COMPONENTS, RegistrationStatuses
from .exports import ExportFileTypes, export_submissions
from .models import (
    Submission,
    SubmissionFileAttachment,
    SubmissionReport,
    SubmissionStep,
    TemporaryFileUpload,
)
from .tasks import on_completion_retry


class SubmissionTypeListFilter(admin.ListFilter):
    title = _("type")
    parameter_name = "type"

    def __init__(self, request, params, model, model_admin):
        super().__init__(request, params, model, model_admin)

        self.request = request

        if self.parameter_name in params:
            value = params.pop(self.parameter_name)
            self.used_parameters[self.parameter_name] = value

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


class SubmissionStepInline(admin.StackedInline):
    model = SubmissionStep
    extra = 0
    fields = (
        "uuid",
        "form_step",
        "data",
    )
    raw_id_fields = ("form_step",)


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
        qs = qs.exclude_tag(TimelineLogTags.AVG)
        return qs.prefetch_related(
            "content_object", "content_object__form"
        ).select_related("user")

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    date_hierarchy = "completed_on"
    list_display = (
        "form",
        "registration_status",
        "last_register_date",
        "successfully_processed",
        "created_on",
        "completed_on",
    )
    list_filter = (SubmissionTypeListFilter, "form")
    search_fields = (
        "form__name",
        "uuid",
        "bsn",
        "kvk",
        "form_url",
        "public_registration_reference",
    )
    inlines = [
        SubmissionStepInline,
        SubmissionPaymentInline,
        SubmissionLogInline,
    ]
    readonly_fields = [
        "created_on",
        "co_sign_data",
        "prefill_data",
        "get_registration_backend",
        "get_appointment_status",
        "get_appointment_id",
        "get_appointment_error_information",
        "on_completion_task_ids",
        "confirmation_email_sent",
        "registration_attempts",
    ]
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

    def successfully_processed(self, obj) -> Optional[bool]:
        if obj.registration_status == RegistrationStatuses.pending:
            return None
        return not obj.needs_on_completion_retry

    successfully_processed.boolean = True
    successfully_processed.short_description = _("Succesfully processed")

    def get_registration_backend(self, obj):
        return obj.form.registration_backend

    get_registration_backend.short_description = _("Registration backend")

    def get_appointment_status(self, obj):
        try:
            return obj.appointment_info.status
        except AppointmentInfo.DoesNotExist:
            return ""

    get_appointment_status.short_description = _("Appointment status")

    def get_appointment_id(self, obj):
        try:
            return obj.appointment_info.appointment_id
        except AppointmentInfo.DoesNotExist:
            return ""

    get_appointment_id.short_description = _("Appointment Id")

    def get_appointment_error_information(self, obj):
        try:
            return obj.appointment_info.error_information
        except AppointmentInfo.DoesNotExist:
            return ""

    get_appointment_error_information.short_description = _(
        "Appointment error information"
    )

    def change_view(self, request, object_id, form_url="", extra_context=None):
        submission = self.get_object(request, object_id)
        submission_details_view_admin(submission, request.user)
        extra_context = {
            "data": submission.get_ordered_data_with_component_type(),
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

        log_export_submissions(queryset.first().form, request.user)
        return export_submissions(queryset, file_type)

    def export_csv(self, request, queryset):
        return self._export(request, queryset, ExportFileTypes.CSV)

    export_csv.short_description = _(
        "Export selected %(verbose_name_plural)s as CSV-file."
    )

    def export_xlsx(self, request, queryset):
        return self._export(request, queryset, ExportFileTypes.XLSX)

    export_xlsx.short_description = _(
        "Export selected %(verbose_name_plural)s as Excel-file."
    )

    def export_json(self, request, queryset):
        return self._export(request, queryset, ExportFileTypes.JSON)

    export_json.short_description = _(
        "Export selected %(verbose_name_plural)s as JSON-file."
    )

    def export_xml(self, request, queryset):
        return self._export(request, queryset, ExportFileTypes.XML)

    export_xml.short_description = _(
        "Export selected %(verbose_name_plural)s as XML-file."
    )

    def retry_processing_submissions(self, request, queryset):
        submissions = queryset.filter(needs_on_completion_retry=True)
        messages.success(
            request,
            ngettext(
                "Retrying processing flow for {count} {verbose_name}",
                "Retrying processing flow for {count} {verbose_name_plural}",
                submissions.count(),
            ).format(
                count=submissions.count(),
                verbose_name=queryset.model._meta.verbose_name,
                verbose_name_plural=queryset.model._meta.verbose_name_plural,
            ),
        )
        for submission in submissions:
            on_completion_retry(submission.id).delay()

    retry_processing_submissions.short_description = _(
        "Retry processing %(verbose_name_plural)s."
    )


@admin.register(SubmissionReport)
class SubmissionReportAdmin(PrivateMediaMixin, admin.ModelAdmin):
    list_display = ("title",)
    list_filter = ("title",)
    search_fields = ("title",)
    raw_id_fields = ("submission",)

    private_media_fields = ("content",)

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
class TemporaryFileUploadAdmin(ReadOnlyAdminMixin, PrivateMediaMixin, admin.ModelAdmin):
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
        "file_name",
        "content_type",
        "created_on",
        "file_size",
    )
    fields = (
        "uuid",
        "submission_step",
        "form_key",
        "created_on",
        "original_name",
        "content_type",
        "file_size",
        "content",
    )
    raw_id_fields = ("submission_step",)
    readonly_fields = (
        "uuid",
        "created_on",
        "file_size",
    )
    date_hierarchy = "created_on"

    private_media_fields = ("content",)
    private_media_view_class = SubmissionFileAttachmentMediaView

    def file_size(self, obj):
        return filesizeformat(obj.content.size)

    file_size.short_description = _("File size")

    def has_add_permission(self, request, obj=None):
        return False
