from django.contrib import admin

from solo.admin import SingletonModelAdmin

from .models import StufDMSConfig


@admin.register(StufDMSConfig)
class StufDMSConfigAdmin(SingletonModelAdmin):
    pass
