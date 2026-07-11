from openforms.forms.api.serializers import FormStepSerializer

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
    pass
