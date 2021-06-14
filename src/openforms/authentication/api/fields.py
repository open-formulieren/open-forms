from rest_framework import serializers

from openforms.authentication.api.serializers import LoginOptionSerializer
from openforms.authentication.registry import register as auth_register


class LoginOptionsReadOnlyField(serializers.ListField):
    """
    the read-mode of the authentication information shows detailed options instead of plugin-ids

    there is no write-mode support because this data is not writable
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("child", LoginOptionSerializer())
        kwargs["read_only"] = True
        kwargs["source"] = "*"
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        raise NotImplementedError("read only")

    def to_representation(self, form):
        request = self.context["request"]
        temp = auth_register.get_options(request, form)
        return super().to_representation(temp)
