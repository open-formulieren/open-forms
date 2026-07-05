from openforms.forms.api.serializers import FormStepSerializer
from openforms.import_export.serializers.base import BaseExportSerializer


class FormStepExportSerializer(FormStepSerializer, BaseExportSerializer):
    pass
