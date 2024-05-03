from django.urls import reverse

from furl import furl

from openforms.forms.models import Form


def get_start_form_url(form: Form, host: str = "") -> str:
    form_path = reverse("core:form-detail", kwargs={"slug": form.slug})
    if not host:
        host = "http://testserver"
    form_url = furl(f"{host}{form_path}").set({"_start": "1"})
    return str(form_url)


def get_start_url(form: Form, plugin_id: str, host: str = "") -> str:
    """
    Build the authentication start URL as constructed by the SDK.
    """
    login_url = reverse(
        "authentication:start",
        kwargs={"slug": form.slug, "plugin_id": plugin_id},
    )
    form_url = get_start_form_url(form, host=host)
    start_url = furl(login_url).set({"next": form_url})
    return str(start_url)
