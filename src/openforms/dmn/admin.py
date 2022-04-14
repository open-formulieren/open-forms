from django.contrib import admin

from .models import DMNEvaluationResult


@admin.register(DMNEvaluationResult)
class DMNEvaluationResultAdmin(admin.ModelAdmin):
    list_display = ("submission", "component", "result")
    list_filter = ("component",)
    search_fields = ("submission__uuid",)
    raw_id_fields = ("submission",)
