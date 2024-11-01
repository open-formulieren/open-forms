from rest_framework import serializers
from rest_framework.request import Request

from openforms.authentication.api.serializers import LoginOptionSerializer
from openforms.authentication.registry import register as auth_register
from openforms.config.models import GlobalConfiguration
from openforms.forms.models import Form


class LoginOptionsReadOnlyField(serializers.ListField):
    """
    the read-mode of the authentication information shows detailed options instead of plugin-ids

    there is no write-mode support because this data is not writable
    """

    def __init__(self, is_for_cosign: bool = False, *args, **kwargs) -> None:
        kwargs.setdefault("child", LoginOptionSerializer())
        kwargs["read_only"] = True
        kwargs["source"] = "*"

        self.is_for_cosign = is_for_cosign

        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        raise NotImplementedError("read only")

    def to_representation(self, value: Form):  # type: ignore reportIncompatibleOverride
        request: Request = self.context["request"]

        options = auth_register.get_options(request, value, self.is_for_cosign)

        # Returning no auth options for cosign if a link is used in the email template
        # results in the cosign block not being shown in the frontend.
        if self.is_for_cosign:
            config = GlobalConfiguration.get_solo()
            if config.cosign_request_template_has_link:
                options = []

        return super().to_representation(options)
