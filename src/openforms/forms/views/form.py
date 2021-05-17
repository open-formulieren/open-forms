from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import urlencode
from django.views.generic import DetailView

from openforms.ui.views.generic import UIDetailView, UIListView

from ..models import Form


class FormListView(UIListView):
    template_name = "core/views/form/form_list.html"
    queryset = Form.objects.filter(_is_deleted=False)


class FormDetailView(UIDetailView):
    template_name = "core/views/form/form_detail.html"
    queryset = Form.objects.filter(_is_deleted=False)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.login_required and not self.request.session.get("bsn"):
            return redirect("forms:form-login", slug=self.kwargs["slug"])
        else:
            return super().get(request, *args, **kwargs)


class FormEditView(DetailView):
    model = Form
    template_name = "core/views/form/form_edit.html"
    pk_url_kwarg = "object_id"
    # set these on the .as_viev(...) call
    admin_site = None
    model_admin = None


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
