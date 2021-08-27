from django.contrib import admin

from solo.admin import SingletonModelAdmin

from .models import AppointmentsConfig


@admin.register(AppointmentsConfig)
class AppointmentsConfigAdmin(SingletonModelAdmin):
    pass
