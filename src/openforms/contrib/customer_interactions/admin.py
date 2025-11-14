from django.contrib import admin

from .models import CustomerInteractionsAPIGroupConfig


@admin.register(CustomerInteractionsAPIGroupConfig)
class CustomerInteractionsAPIGroupConfigAdmin(admin.ModelAdmin):
    search_fields = (
        "name",
        "identifier",
    )
    raw_id_fields = ("customer_interactions_service",)
    prepopulated_fields = {"identifier": ["name"]}
