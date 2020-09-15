from django.contrib import admin

from openforms.core.models import FormSubmission


class FormSubmissionAdmin(admin.ModelAdmin):
    pass


admin.site.register(FormSubmission, FormSubmissionAdmin)
