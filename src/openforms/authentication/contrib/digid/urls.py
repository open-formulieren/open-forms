from django.urls import path, resolve

from digid_eherkenning.views import DigiDLoginView as _DigiDLoginView
from furl import furl

from openforms.forms.models import Form

from .views import DigiDAssertionConsumerServiceView

app_name = "digid"


class DigiDLoginView(_DigiDLoginView):
    def get_level_of_assurance(self):
        return_path = furl(self.request.GET.get("next")).path
        _, _, kwargs = resolve(return_path)

        form = Form.objects.get(slug=kwargs.get("slug"))

        loa = form.authentication_backend_options.get(app_name, {}).get("loa")
        return loa if loa else super().get_level_of_assurance()


urlpatterns = [
    path("login/", DigiDLoginView.as_view(), name="login"),
    path("acs/", DigiDAssertionConsumerServiceView.as_view(), name="acs"),
]
