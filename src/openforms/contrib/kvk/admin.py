from django.contrib import admin

from solo.admin import SingletonModelAdmin

from .models import KVKConfig


@admin.register(KVKConfig)
class KVKConfigAdmin(SingletonModelAdmin):
    pass
