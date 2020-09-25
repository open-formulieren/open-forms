from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import urlencode

from openforms.core.models import Form
from openforms.ui.views.generic import UIDetailView, UIListView


class FormListView(UIListView):
    model = Form
    template_name = 'core/views/form/form_list.html'


class FormDetailView(UIDetailView):
    model = Form
    template_name = 'core/views/form/form_detail.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.login_required and not self.request.session.get('bsn'):
            return redirect('core:form-login', slug=self.kwargs['slug'])
        else:
            return super().get(request, *args, **kwargs)


class FormLoginButtonView(UIDetailView):
    model = Form
    template_name = 'core/views/form/form_login.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.request.GET.get('bsn'):
            self.request.session['bsn'] = self.request.GET['bsn']
            url = self.request.GET.get('next')
            if not url:
                url = self.object.get_absolute_url()
            return redirect(url)
        else:
            return super().get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)

        # NOTE: we dont use the User creation feature so we bypass the regular ACS and use this view instead
        url = reverse('digid-mock:login')
        params = {
            "acs": self.request.path,
            "next": self.object.get_absolute_url(),
            "cancel": self.object.get_absolute_url(),
        }
        ctx.update({
            'digid_button_url': f"{url}?{urlencode(params)}"
        })
        return ctx
