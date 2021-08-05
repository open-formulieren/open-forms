from django.contrib import admin, messages
from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext_lazy as _, ngettext

from privates.admin import PrivateMediaMixin
from privates.views import PrivateMediaView

from openforms.payments.models import SubmissionPayment
from openforms.registrations.tasks import register_submission
from .constants import IMAGE_COMPONENTS
from .constants import RegistrationStatuses
from .exports import export_submissions
from .models import (
    Submission,
    SubmissionFileAttachment,
    SubmissionReport,
    SubmissionStep,
    TemporaryFileUpload,
)


class SubmissionStepInline(admin.StackedInline):
    model = SubmissionStep
    extra = 0
    fields = (
        "uuid",
        "form_step",
        "data",
    )


class SubmissionPaymentInline(admin.StackedInline):
    model = SubmissionPayment
    extra = 0
    fields = (
        "uuid",
        "created",
        "submission",
        "plugin_id",
        "form_url",
        "order_id",
        "amount",
        "status",
    )
    readonly_fields = (
        "uuid",
        "created",
        "submission",
        "plugin_id",
        "form_url",
        "order_id",
        "amount",
        "status",
    )

    def has_add_permission(self, request, obj=None):
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
        "created_on",
        "completed_on",
    )
    list_filter = ("form",)
    search_fields = ("form__name",)
    inlines = [
        SubmissionStepInline,
        SubmissionPaymentInline,
    ]
    readonly_fields = [
        "created_on",
        "get_registration_backend",
    ]
    actions = ["export_csv", "export_xlsx", "resend_submissions"]

    def get_registration_backend(self, obj):
        return obj.form.registration_backend

    get_registration_backend.short_description = _("Registration Backend")

    def change_view(self, request, object_id, form_url="", extra_context=None):
        submission = self.get_object(request, object_id)
        extra_context = {
            "data": submission.data_with_component_type,
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

        return export_submissions(queryset, file_type)

    def export_csv(self, request, queryset):
        return self._export(request, queryset, "csv")

    export_csv.short_description = _(
        "Export selected %(verbose_name_plural)s as CSV-file."
    )

    def export_xlsx(self, request, queryset):
        return self._export(request, queryset, "xlsx")

    export_xlsx.short_description = _(
        "Export selected %(verbose_name_plural)s as Excel-file."
    )

    def resend_submissions(self, request, queryset):
        submissions = queryset.filter(registration_status=RegistrationStatuses.failed)
        messages.success(
            request,
            ngettext(
                "Resending {count} {verbose_name} to registration backend",
                "Resending {count} {verbose_name_plural} to registration backend",
                submissions.count(),
            ).format(
                count=submissions.count(),
                verbose_name=queryset.model._meta.verbose_name,
                verbose_name_plural=queryset.model._meta.verbose_name_plural,
            ),
        )
        for submission in submissions:
            register_submission.delay(submission.id)

    resend_submissions.short_description = _(
        "Resend %(verbose_name_plural)s to the registration backend."
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
        "file_size",
    )
    date_hierarchy = "created_on"

    private_media_fields = ("content",)
    private_media_view_class = TemporaryFileUploadMediaView

    def file_size(self, obj):
        return filesizeformat(obj.content.size)

    file_size.short_description = _("File size")

    def has_add_permission(self, request, obj=None):
        return False


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
