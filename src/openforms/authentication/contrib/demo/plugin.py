from django import forms
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseRedirect,
)
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from openforms.forms.models import Form
from openforms.utils.validators import BSNValidator

from ...base import BasePlugin, CosignSlice
from ...constants import CO_SIGN_PARAMETER, FORM_AUTH_SESSION_KEY, AuthAttribute
from ...exceptions import InvalidCoSignData
from ...registry import register


class DemoBaseForm(forms.Form):
    next = forms.URLField(required=True, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[CO_SIGN_PARAMETER] = forms.UUIDField(
            required=False, widget=forms.HiddenInput
        )


class BSNForm(DemoBaseForm):
    bsn = forms.CharField(
        max_length=9, required=True, label=_("BSN"), validators=[BSNValidator()]
    )


class KVKForm(DemoBaseForm):
    # TODO add kvk-number validator from validation branches kvk app
    kvk = forms.CharField(
        max_length=9,
        required=True,
        label=_("KvK number"),
    )


class DemoBaseAuthentication(BasePlugin):
    verbose_name = _("Demo")
    return_method = "POST"
    form_class: type = NotImplemented
    is_demo_plugin = True

    def start_login(
        self, request: HttpRequest, form: Form, form_url: str, options
    ) -> str | HttpResponse:
        context = {
            "form_action": self.get_return_url(request, form),
            "form_url": form_url,
            "form": self.form_class(
                initial={
                    "next": form_url,
                    CO_SIGN_PARAMETER: request.GET.get(CO_SIGN_PARAMETER),
                }
            ),
        }
        return render(request, "authentication/contrib/demo/login.html", context)

    def handle_co_sign(self, request: HttpRequest, form: Form) -> CosignSlice:
        submitted = self.form_class(request.POST)
        if not submitted.is_valid():
            raise InvalidCoSignData(f"Validation errors: {submitted.errors}")
        identifier = submitted.cleaned_data[self.form_field]
        return {
            "identifier": identifier,
            "fields": {},
        }

    def handle_return(
        self, request: HttpRequest, form: Form, options
    ) -> str | HttpResponse:
        submitted = self.form_class(request.POST)
        if not submitted.is_valid():
            return HttpResponseBadRequest("invalid data")

        # set the session auth key only if we're not co-signing
        is_co_sign = bool(submitted.cleaned_data.get(CO_SIGN_PARAMETER))
        if not is_co_sign:
            request.session[FORM_AUTH_SESSION_KEY] = {
                "plugin": self.identifier,
                "attribute": self.provides_auth[0],
                "value": submitted.cleaned_data[self.provides_auth[0]],
            }

        return HttpResponseRedirect(submitted.cleaned_data["next"])


# client requested demo and demo-kvk to no longer be 'demo' (Github #805), but that
# conflicts with the required admin/staff user check from #1322. This has been
# overruled, as demo plugins can be enabled via a feature flag and other demo plugins
# can be disabled in the global configuration if considered annoying (see #1103).


@register("demo")
class DemoBSNAuthentication(DemoBaseAuthentication):
    verbose_name = _("Demo BSN")
    form_class = BSNForm
    provides_auth = (AuthAttribute.bsn,)
    form_field = "bsn"
    is_demo_plugin = True


@register("demo-kvk")
class DemoKVKAuthentication(DemoBaseAuthentication):
    verbose_name = _("Demo KvK number")
    form_class = KVKForm
    provides_auth = (AuthAttribute.kvk,)
    form_field = "kvk"
    is_demo_plugin = True
