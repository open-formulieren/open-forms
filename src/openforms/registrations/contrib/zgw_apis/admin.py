from django.contrib import admin

from .models import ZGWApiGroupConfig


@admin.register(ZGWApiGroupConfig)
class ZGWApiGroupConfigAdmin(admin.ModelAdmin):
    list_display = ("name", "zrc_service", "drc_service", "ztc_service")
    list_select_related = ("zrc_service", "drc_service", "ztc_service")
    search_fields = ("name",)
    raw_id_fields = ("zrc_service", "drc_service", "ztc_service")
    ordering = ("name",)
