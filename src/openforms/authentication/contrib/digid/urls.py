from django.urls import path, resolve

from digid_eherkenning.views import DigiDLoginView as _DigiDLoginView
from furl import furl

from openforms.forms.models import Form

from .views import DigiDAssertionConsumerServiceView

app_name = "digid"


class DigiDLoginView(_DigiDLoginView):
    def get_level_of_assurance(self):
        return_url = furl(self.request.GET.get("next"))
        form_path = furl(return_url.args["next"]).path

        resolver_match = resolve(form_path)
        form_slug = resolver_match.kwargs.get("slug")

        form = Form.objects.get(slug=form_slug)

        loa = form.authentication_backend_options.get("digid", {}).get("loa")
        return loa if loa else super().get_level_of_assurance()


urlpatterns = [
    path("login/", DigiDLoginView.as_view(), name="login"),
    path("acs/", DigiDAssertionConsumerServiceView.as_view(), name="acs"),
]
