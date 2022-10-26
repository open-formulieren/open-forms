from django.utils.translation import gettext_lazy as _

from rest_framework import serializers


class AllOrNoneRequiredFieldsValidator:
    """
    Validate that the set of fields is present as soon as one field is provided.

    Field values are checked to be truthy to determine if they are provided or not.
    """

    message = _("The fields {fields} must all be provided if one of them is provided.")
    code = "required"
    requires_context = True

    def __init__(self, *fields: str):
        self.fields = fields

    def __call__(self, data: dict, serializer: serializers.Serializer):
        values = [data.get(field) for field in self.fields]
        if any(values) and not all(values):
            err = self.message.format(fields=", ".join(self.fields))
            raise serializers.ValidationError(err, code=self.code)
