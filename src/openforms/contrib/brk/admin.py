from django.contrib import admin

from solo.admin import SingletonModelAdmin

from .models import BRKConfig


@admin.register(BRKConfig)
class BRKConfigAdmin(SingletonModelAdmin):
    pass
