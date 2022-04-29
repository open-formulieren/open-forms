from urllib.parse import urlsplit

from django.conf import settings
from django.http import HttpRequest
from django.test import RequestFactory
from django.urls import reverse


def get_request() -> HttpRequest:
    """
    Build a mock request.

    :meta private:
    """
    base = urlsplit(settings.BASE_URL)
    request = RequestFactory().get(
        reverse("core:form-list"),
        HTTP_HOST=base.netloc,
        **{"wsgi.url_scheme": base.scheme},
    )
    return request
