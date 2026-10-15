from ...api.serializers import FormStepSerializer
from ...models import FormStep, FormVariable
from ..typing import FormStepData
from .base import BaseExportSerializer, BaseImportSerializer


class FormStepExportSerializer(
    FormStepSerializer, BaseExportSerializer[FormStep, FormStepData]
):
    safe_export_fields = (
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
        "previous_text",
        "save_text",
        "next_text",
        "translations",
    )


class FormStepImportSerializer(
    FormStepSerializer, BaseImportSerializer[FormStep, FormStepData]
):
    def after_import(self, instance: FormStep) -> FormStep:
        if (form := self.context.get("form")) is not None:
            # Once the form steps have been created, we create the component FormVariables
            # based on the form definition configurations.
            FormVariable.objects.create_for_form(form)

        return instance
