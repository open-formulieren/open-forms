from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from openforms.forms.models import FormDefinition


class FormDefinitionValidator:
    code = "non-existant-form-definition"
    message = _("A form definition does not exist with this uuid")

    def set_context(self, serializer):
        """
        This hook is called by the serializer instance,
        prior to the validation call being made.
        """
        self.instance = getattr(serializer, "instance", None)

    def __call__(self, attrs: dict):
        if (
            not attrs.get("form_definition")
            or not FormDefinition.objects.filter(uuid=attrs["form_definition"]).exists()
        ):
            raise ValidationError(self.message, code=self.code)
