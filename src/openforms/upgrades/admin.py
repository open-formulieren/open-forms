from django.contrib import admin

from solo.admin import SingletonModelAdmin

from .models import VersionInfo


@admin.register(VersionInfo)
class VersionInfoAdmin(SingletonModelAdmin):
    pass
