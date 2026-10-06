from ...api.serializers import FormStepSerializer
from ...models import FormStep
from ..typing import FormStepDataRepresentation
from .base import BaseExportSerializer, BaseImportSerializer


class FormStepExportSerializer(
    FormStepSerializer, BaseExportSerializer[FormStep, FormStepDataRepresentation]
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
    FormStepSerializer, BaseImportSerializer[FormStepDataRepresentation]
):
    pass
