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
from openforms.authentication.registry import register
from openforms.forms.models import Form


class BSNForm(forms.Form):
    bsn = forms.CharField(max_length=9, required=True, label=_("BSN"))
    next = forms.URLField(required=True, widget=forms.HiddenInput)


@register("demo")
class DemoAuthentication(BasePlugin):
    verbose_name = _("Demo")
    return_method = "POST"

    def start_login(
        self, request: HttpRequest, form: Form, form_url: str
    ) -> Union[str, HttpResponse]:
        context = {
            "form_action": self.get_return_url(request, form),
            "form_url": form_url,
            "form": BSNForm(initial={"next": form_url}),
        }
        return render(request, "authentication/contrib/demo/login.html", context)

    def handle_return(
        self, request: HttpRequest, form: Form
    ) -> Union[str, HttpResponse]:
        submited = BSNForm(request.POST)
        if not submited.is_valid():
            return HttpResponseBadRequest("invalid data")

        request.session["bsn"] = submited.cleaned_data["bsn"]

        return HttpResponseRedirect(submited.cleaned_data["next"])
        0
