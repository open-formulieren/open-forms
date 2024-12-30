from django.contrib import admin

from solo.admin import SingletonModelAdmin

from .models import JSONConfig


@admin.register(JSONConfig)
class JSONConfigAdmin(SingletonModelAdmin):
    pass
