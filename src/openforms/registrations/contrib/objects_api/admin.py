from django.contrib import admin

from solo.admin import SingletonModelAdmin

from .models import ObjectsAPIConfig


@admin.register(ObjectsAPIConfig)
class ObjectsAPIConfigAdmin(SingletonModelAdmin):
    pass
