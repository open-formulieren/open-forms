from django.contrib import admin

from solo.admin import SingletonModelAdmin

from .models import SuwinetConfig


@admin.register(SuwinetConfig)
class SuwinetConfigAdmin(SingletonModelAdmin):
    pass
