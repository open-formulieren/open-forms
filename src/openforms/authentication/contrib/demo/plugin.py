from typing import Union

from django import forms
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseRedirect,
)
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from openforms.authentication.base import BasePlugin
from openforms.authentication.constants import AuthAttribute
from openforms.authentication.registry import register
from openforms.forms.models import Form
from openforms.utils.validators import BSNValidator


class DemoBaseForm(forms.Form):
    next = forms.URLField(required=True, widget=forms.HiddenInput)


class BSNForm(DemoBaseForm):
    bsn = forms.CharField(
        max_length=9, required=True, label=_("BSN"), validators=[BSNValidator]
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
    provides_auth: str = NotImplemented
    is_demo_plugin = True

    def start_login(
        self, request: HttpRequest, form: Form, form_url: str
    ) -> Union[str, HttpResponse]:
        context = {
            "form_action": self.get_return_url(request, form),
            "form_url": form_url,
            "form": self.form_class(initial={"next": form_url}),
        }
        return render(request, "authentication/contrib/demo/login.html", context)

    def handle_return(
        self, request: HttpRequest, form: Form
    ) -> Union[str, HttpResponse]:
        submitted = self.form_class(request.POST)
        if not submitted.is_valid():
            return HttpResponseBadRequest("invalid data")

        request.session["form_auth"] = {
            "plugin": self.identifier,
            "attribute": self.provides_auth,
            "value": submitted.cleaned_data[self.provides_auth],
        }

        return HttpResponseRedirect(submitted.cleaned_data["next"])


@register("demo")
class DemoBSNAuthentication(DemoBaseAuthentication):
    verbose_name = _("Demo BSN")
    form_class = BSNForm
    provides_auth = AuthAttribute.bsn
    form_field = "bsn"

    # client requested this to no longer be demo (Github #805)
    is_demo_plugin = False


@register("demo-kvk")
class DemoKVKAuthentication(DemoBaseAuthentication):
    verbose_name = _("Demo KvK number")
    form_class = KVKForm
    provides_auth = AuthAttribute.kvk
    form_field = "kvk"

    # client requested this to no longer be demo (Github #805)
    is_demo_plugin = False
