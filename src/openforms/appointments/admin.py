from django.contrib import admin

from solo.admin import SingletonModelAdmin

from .models import AppointmentInfo, AppointmentsConfig


@admin.register(AppointmentsConfig)
class AppointmentsConfigAdmin(SingletonModelAdmin):
    pass


class AppointmentInfoInline(admin.StackedInline):
    model = AppointmentInfo
    extra = 0
