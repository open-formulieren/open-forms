from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from openforms.payments.models import SubmissionPayment

from .fields import PaymentBackendChoiceField


class PaymentBackendChoiceFieldMixin:
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if isinstance(db_field, PaymentBackendChoiceField):
            assert not db_field.choices
            _old = db_field.choices
            db_field.choices = db_field._get_plugin_choices()
            field = super().formfield_for_dbfield(db_field, request, **kwargs)
            db_field.choices = _old
            return field

        return super().formfield_for_dbfield(db_field, request, **kwargs)


@admin.register(SubmissionPayment)
class SubmissionPaymentAdmin(admin.ModelAdmin):
    fields = (
        "uuid",
        "created",
        "submission",
        "plugin_id",
        "plugin_options",
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
        "order_id_str",
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

    def order_id_str(self, obj):
        return str(obj.order_id)

    order_id_str.short_description = _("Order ID")
    order_id_str.admin_order_field = "order_id"
