from django.contrib import admin, messages
from django.template.defaultfilters import filesizeformat
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from privates.admin import PrivateMediaMixin
from rest_framework.permissions import IsAdminUser

from .constants import IMAGE_COMPONENTS
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


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    date_hierarchy = "completed_on"
    list_display = (
        "form",
        "registration_status",
        "created_on",
        "completed_on",
    )
    list_filter = ("form",)
    search_fields = ("form__name",)
    inlines = [
        SubmissionStepInline,
    ]
    readonly_fields = ["created_on"]
    actions = ["export_csv", "export_xlsx"]

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


@admin.register(SubmissionReport)
class SubmissionReportAdmin(PrivateMediaMixin, admin.ModelAdmin):
    list_display = ("title",)
    list_filter = ("title",)
    search_fields = ("title",)
    raw_id_fields = ("submission",)

    private_media_fields = ("content",)

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(TemporaryFileUpload)
class TemporaryFileUploadAdmin(admin.ModelAdmin):
    list_display = ("uuid", "file_name", "content_type", "created_on")
    fields = ("uuid", "created_on", "filename_url", "content_type", "file_size")

    search_fields = ("uuid",)
    readonly_fields = (
        "filename_url",
        "file_size",
    )
    date_hierarchy = "created_on"

    def filename_url(self, obj):
        url = reverse("admin_upload_retrieve", kwargs={"uuid": obj.uuid})
        return format_html('<a href="{u}">{n}</a>', u=url, n=obj.file_name)

    filename_url.allow_tags = True
    filename_url.short_description = _("File name")

    def file_size(self, obj):
        return filesizeformat(obj.content.size)

    file_size.allow_tags = True
    file_size.short_description = _("File size")

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(SubmissionFileAttachment)
class SubmissionFileAttachmentAdmin(admin.ModelAdmin):
    fields = (
        "uuid",
        "submission_step",
        "form_key",
        "created_on",
        "filename_url",
        "original_name",
        "content_type",
        "file_size",
    )
    readonly_fields = (
        "filename_url",
        "file_size",
    )
    date_hierarchy = "created_on"

    def filename_url(self, obj):
        url = reverse("admin_attachment_retrieve", kwargs={"uuid": obj.uuid})
        return format_html('<a href="{u}">{n}</a>', u=url, n=obj.get_display_name())

    filename_url.allow_tags = True
    filename_url.short_description = _("File name")

    def file_size(self, obj):
        return filesizeformat(obj.content.size)

    file_size.allow_tags = True
    file_size.short_description = _("File size")

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
