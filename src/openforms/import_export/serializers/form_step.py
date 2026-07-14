from openforms.forms.api.serializers import FormStepSerializer
from openforms.forms.models import FormVariable
from openforms.import_export.serializers.base import (
    BaseExportSerializer,
    BaseImportSerializer,
)


class FormStepExportSerializer(FormStepSerializer, BaseExportSerializer):
    pass


class FormStepImportSerializer(FormStepSerializer, BaseImportSerializer):
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if (form := self.context.get("form")) is not None:
            # Once the form steps have been created, we create the component
            # FormVariables based on the form definition configurations.
            FormVariable.objects.create_for_form(form)
