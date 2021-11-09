from django.contrib import admin

from .models import MSGraphService


@admin.register(MSGraphService)
class MSGraphServiceAdmin(admin.ModelAdmin):
    pass
