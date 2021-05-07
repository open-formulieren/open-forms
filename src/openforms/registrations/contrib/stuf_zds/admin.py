from django.contrib import admin

from solo.admin import SingletonModelAdmin

from .models import SoapService, StufZDSConfig


@admin.register(StufZDSConfig)
class StufZDSConfigAdmin(SingletonModelAdmin):
    pass


@admin.register(SoapService)
class SoapServiceAdmin(admin.ModelAdmin):
    pass
