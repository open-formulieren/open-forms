from contextlib import contextmanager
from unittest.mock import PropertyMock, patch

from django.http import HttpResponse, HttpResponseRedirect

from rest_framework import serializers

from ..base import BasePlugin
from ..constants import AuthAttribute
from ..registry import Registry


class Plugin(BasePlugin):
    verbose_name = "some human readable label"
    provides_auth = (AuthAttribute.bsn,)

    def start_login(self, request, form, form_url, options):
        return HttpResponse("start")

    def handle_return(self, request, form, options):
        return HttpResponseRedirect(request.GET.get("next"))

    def handle_co_sign(self, request, form):
        return {
            "identifier": "mock-id",
            "fields": {
                "mock_field_1": "field 1",
                "mock_field_2": "",
            },
        }


class FailingPlugin(BasePlugin):
    verbose_name = "some human readable label"

    def start_login(self, request, form, form_url, options):
        raise Exception("start")

    def handle_return(self, request, form, options):
        raise Exception("return")


class RequiresAdminPlugin(BasePlugin):
    verbose_name = "plugin requiring staff user session"
    provides_auth = (AuthAttribute.bsn,)
    is_demo_plugin = True

    def start_login(self, request, form, form_url, options):
        return HttpResponse("start")

    def handle_return(self, request, form, options):
        return HttpResponseRedirect(request.GET.get("next"))

    def handle_co_sign(self, request, form):
        return {
            "identifier": "mock-id",
            "fields": {
                "mock_field_1": "field 1",
                "mock_field_2": "",
            },
        }


class FailingSerializer(serializers.Serializer):
    def validate(self, attrs):
        raise serializers.ValidationError("always fails")


class BadConfigurationOptionsPlugin(Plugin):
    configuration_options = FailingSerializer


@contextmanager
def mock_register(register: Registry):
    patcher1 = patch(
        "openforms.authentication.views.AuthenticationStartView.register",
        new_callable=PropertyMock,
        return_value=register,
    )
    patcher2 = patch(
        "openforms.authentication.views.AuthenticationReturnView.register",
        new_callable=PropertyMock,
        return_value=register,
    )
    patcher3 = patch("openforms.submissions.serializers.register", new=register)
    patcher4 = patch("openforms.authentication.signals.register", new=register)
    with patcher1, patcher2, patcher3, patcher4:
        yield
