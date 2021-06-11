from rest_framework import serializers

from openforms.authentication.api.serializers import LoginOptionSerializer
from openforms.authentication.registry import register as auth_register


class LoginOptionsReadOnlyField(serializers.ListField):
    """
    the read part of the authentication information shows detailed options instead of plugin-ids
    """

    def __init__(self, *args, **kwargs):
        kwargs["child"] = LoginOptionSerializer()
        kwargs["read_only"] = True
        kwargs["source"] = "*"
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        raise NotImplementedError("read only")

    def to_representation(self, form):
        request = self.context["request"]
        temp = auth_register.get_options(request, form)
        return super().to_representation(temp)
