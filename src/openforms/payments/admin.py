from django.contrib import admin

from openforms.payments.models import SubmissionPayment


@admin.register(SubmissionPayment)
class SubmissionPaymentAdmin(admin.ModelAdmin):
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
    raw_id_fields = ("submission",)
    readonly_fields = (
        "uuid",
        "created",
    )
    list_display = (
        "uuid",
        "created",
        "submission",
        "plugin_id",
        "order_id",
        "amount",
        "status",
    )
    list_filter = ("status",)
    search_fields = (
        "order_id",
        "submission__uuid",
        "uuid",
        "form_url",
    )
