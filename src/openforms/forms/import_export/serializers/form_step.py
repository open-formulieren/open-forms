from openforms.forms.api.serializers import FormStepSerializer
from openforms.forms.models import FormVariable

from .base import BaseExportSerializer, BaseImportSerializer


class FormStepExportSerializer(FormStepSerializer, BaseExportSerializer):
    save_export_fields = (
        "uuid",
        "index",
        "slug",
        "configuration",
        "form_definition",
        "name",
        "internal_name",
        "url",
        "is_applicable",
        "login_required",
        "is_reusable",
        "literals",
        "previous_text",
        "save_text",
        "next_text",
        "translations",
    )


class FormStepImportSerializer(FormStepSerializer, BaseImportSerializer):
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if (form := self.context.get("form")) is not None:
            # Once the form steps have been created, we create the component
            # FormVariables based on the form definition configurations.
            FormVariable.objects.create_for_form(form)
