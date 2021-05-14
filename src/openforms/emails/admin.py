from django.contrib import admin

from .forms import ConfirmationEmailTemplateForm
from .models import ConfirmationEmailTemplate


@admin.register(ConfirmationEmailTemplate)
class ConfirmationEmailTemplateAdmin(admin.ModelAdmin):
    form = ConfirmationEmailTemplateForm
