from django.contrib import admin

from .models import IITPrefillTestCase


@admin.register(IITPrefillTestCase)
class IITPrefillTestCaseAdmin(admin.ModelAdmin):
    list_display = ("bsn", "test")
    search_fields = ("bsn", "test")
