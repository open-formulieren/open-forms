from django.contrib import admin

from .models import SubmissionPayment


@admin.register(SubmissionPayment)
class SubmissionPaymentAdmin(admin.ModelAdmin):
    fields = (
        "uuid",
        "created",
        "submission",
        "plugin_id",
        "plugin_options",
        "public_order_id",
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
        "public_order_id",
        "amount",
        "status",
    )
    list_filter = ("status",)
    search_fields = (
        "public_order_id",
        "submission__uuid",
        "uuid",
    )
