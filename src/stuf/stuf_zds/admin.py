from django.contrib import admin

from solo.admin import SingletonModelAdmin

from .models import StufZDSConfig


@admin.register(StufZDSConfig)
class StufZDSConfigAdmin(SingletonModelAdmin):
    pass
