from django.http import HttpResponseBadRequest
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import urlencode
from django.views.generic import RedirectView

from openforms.ui.views.generic import UIDetailView, UIListView

from ..models import Form


class FormListView(UIListView):
    template_name = "core/views/form/form_list.html"
    queryset = Form.objects.filter(_is_deleted=False)


class FormDetailView(UIDetailView):
    template_name = "core/views/form/form_detail.html"
    queryset = Form.objects.filter(_is_deleted=False)


class FormLoginButtonView(UIDetailView):
    model = Form
    template_name = "core/views/form/form_login.html"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.request.GET.get("bsn"):
            self.request.session["bsn"] = self.request.GET["bsn"]
            url = self.request.GET.get("next")
            if not url:
                url = self.object.get_absolute_url()
            return redirect(url)
        else:
            return super().get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)

        # NOTE: we dont use the User creation feature so we bypass
        # the regular ACS and use this view instead
        url = reverse("digid-mock:login")
        params = {
            "acs": self.request.path,
            "next": self.object.get_absolute_url(),
            "cancel": self.object.get_absolute_url(),
        }
        ctx.update({"digid_button_url": f"{url}?{urlencode(params)}"})
        return ctx


class DigidStartRedirectView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        form_url = self.request.GET.get("next")
        if not form_url:
            return HttpResponseBadRequest("missing 'next' parameter")

        url = reverse("digid-mock:login")
        params = {
            "acs": self.request.build_absolute_uri(reverse("digid-login-return")),
            "next": form_url,
            "cancel": form_url,
        }
        url = f"{url}?{urlencode(params)}"
        return url


class DigidReturnRedirectView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        if self.request.GET.get("bsn"):
            self.request.session["bsn"] = self.request.GET["bsn"]
        else:
            return HttpResponseBadRequest("missing 'bsn' parameter")

        url = self.request.GET.get("next")
        if not url:
            return HttpResponseBadRequest("missing 'next' parameter")
        else:
            return url
