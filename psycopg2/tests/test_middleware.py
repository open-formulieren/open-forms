from django.test import RequestFactory

import pytest

from mozilla_django_oidc_db.middleware import SessionRefresh
from mozilla_django_oidc_db.models import OpenIDConnectConfig


@pytest.mark.django_db
def test_sessionrefresh_oidc_not_enabled():
    config = OpenIDConnectConfig.get_solo()

    config.enabled = False
    config.save()

    request = RequestFactory().get("/")

    # Running the middleware should return None, since OIDC is disabled
    result = SessionRefresh(get_response=lambda: None).process_request(request)

    assert result is None
