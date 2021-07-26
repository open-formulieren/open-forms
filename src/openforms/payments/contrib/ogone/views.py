import time

from django import forms
from django.views.generic import TemplateView

from openforms.payments.contrib.ogone.data import OgoneRequestParams
from openforms.payments.contrib.ogone.signing import calculate_shasign


class DevView(TemplateView):
    """
    temporary view for dev
    TODO remove before merge
    """

    template_name = "ogone/dev.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        url = "https://ogone.test.v-psp.com/ncol/test/orderstandard_utf8.asp"

        params = OgoneRequestParams(
            AMOUNT=1500,
            CURRENCY="EUR",
            LANGUAGE="en_US",
            ORDERID=1234,
            PSPID="MyPSPID",
        )
        passphrase = "Mysecretsig1875!?"

        params = OgoneRequestParams(
            AMOUNT=1500,
            CURRENCY="EUR",
            LANGUAGE="nl_NL",
            ORDERID=f"TEST001-{int(time.time())}",
            PSPID="maykinmedia",
        )
        passphrase = "10347d2a-7ef7-4462-9c3b-febf7b813a6a"
        data = params.get_dict()
        data["SHASIGN"] = calculate_shasign(data, passphrase, "sha512")

        # widget = forms.HiddenInput

        fields = {name: forms.CharField(initial=value) for name, value in data.items()}
        Form = type("MyForm", (forms.Form,), fields)
        ctx["payment"] = {
            "url": url,
            "form": Form(),
        }
        return ctx
