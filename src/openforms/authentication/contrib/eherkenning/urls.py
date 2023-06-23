from django.urls import path, resolve

from digid_eherkenning.views import eHerkenningLoginView as _eHerkenningLoginView
from furl import furl

from openforms.forms.models import Form

from .views import eHerkenningAssertionConsumerServiceView

app_name = "eherkenning"


class eHerkenningLoginView(_eHerkenningLoginView):
    def get_level_of_assurance(self):
        # get the form_slug from /auth/{slug}/...?next=...
        return_path = furl(self.request.GET.get("next")).path
        _, _, kwargs = resolve(return_path)

        form = Form.objects.get(slug=kwargs.get("slug"))

        loa = form.authentication_backend_options.get(app_name, {}).get("loa")
        return loa if loa else super().get_level_of_assurance()


urlpatterns = [
    path("login/", eHerkenningLoginView.as_view(), name="login"),
    path("acs/", eHerkenningAssertionConsumerServiceView.as_view(), name="acs"),
]
