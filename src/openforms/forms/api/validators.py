from django.core.exceptions import ValidationError
from django.http import Http404
from django.utils.translation import ugettext_lazy as _

from openforms.forms.models import Form, FormDefinition


class FormValidator:

    def set_context(self, serializer):
        """
        This hook is called by the serializer instance,
        prior to the validation call being made.
        """
        self.form_uuid = serializer.context["view"].kwargs["form_uuid"]

    def __call__(self, attrs: dict):
        if not Form.objects.filter(uuid=self.form_uuid).exists():
            raise Http404()


class FormDefinitionValidator:
    code = "non-existant-form-definition"
    message = _("A form definition does not exist with this uuid")

    def __call__(self, attrs: dict):
        if (
            not attrs.get("form_definition")
            or not FormDefinition.objects.filter(uuid=attrs["form_definition"]).exists()
        ):
            raise ValidationError(self.message, code=self.code)
