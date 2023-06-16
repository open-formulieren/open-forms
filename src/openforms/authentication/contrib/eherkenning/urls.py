from django.urls import path, resolve

from digid_eherkenning.views import eHerkenningLoginView as _eHerkenningLoginView
from furl import furl

from openforms.forms.models import Form

from .views import eHerkenningAssertionConsumerServiceView

app_name = "eherkenning"


class eHerkenningLoginView(_eHerkenningLoginView):
    def get_level_of_assurance(self):
        return_url = furl(self.request.GET.get("next"))
        form_path = furl(return_url.args["next"]).path

        resolver_match = resolve(form_path)
        form_slug = resolver_match.kwargs.get("slug")

        form = Form.objects.get(slug=form_slug)

        loa = form.authentication_backend_options.get("eherkenning", {}).get("loa")
        return loa if loa else super().get_level_of_assurance()


urlpatterns = [
    path("login/", eHerkenningLoginView.as_view(), name="login"),
    path("acs/", eHerkenningAssertionConsumerServiceView.as_view(), name="acs"),
]
