from django.contrib import admin

from .models import CustomerInteractionsAPIGroupConfig


@admin.register(CustomerInteractionsAPIGroupConfig)
class CustomerInteractionsAPIGroupConfigAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "identifier",
        "customer_interactions_service",
    )
    list_select_related = ("customer_interactions_service",)
    search_fields = (
        "name",
        "identifier",
    )
    raw_id_fields = ("customer_interactions_service",)
    prepopulated_fields = {"identifier": ["name"]}
