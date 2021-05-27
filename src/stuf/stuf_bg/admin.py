from django.contrib import admin

from solo.admin import SingletonModelAdmin

from .models import StufBGConfig


@admin.register(StufBGConfig)
class StufBGConfigAdmin(SingletonModelAdmin):
    pass
