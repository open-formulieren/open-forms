from openforms.forms.api.serializers import FormStepSerializer
from openforms.import_export.serializers.base import (
    BaseExportSerializer,
    BaseImportSerializer,
)


class FormStepExportSerializer(FormStepSerializer, BaseExportSerializer):
    pass


class FormStepImportSerializer(FormStepSerializer, BaseImportSerializer):
    pass
