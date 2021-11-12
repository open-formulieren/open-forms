from django.contrib import admin

from .models import MSGraphService


@admin.register(MSGraphService)
class MSGraphServiceAdmin(admin.ModelAdmin):
    list_display = ("label", "tenant_id", "client_id")
    search_fields = ("label", "tenant_id", "client_id")
