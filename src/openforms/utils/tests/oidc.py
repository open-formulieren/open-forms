from contextlib import contextmanager
from unittest.mock import patch

from mozilla_django_oidc_db.models import OIDCClient, OIDCProvider


class OIDCMixin:
    """
    Helpers around mozilla-django-oidc and mozilla-django-oidc-db.

    The post-migrate hook populates the pre-defined OIDC clients and providers, which
    makes the developer experience in (unit) tests worse because you can't easily update
    or patch the configurations, since the factories perform a get_or_create rather than
    update_or_create. We resolve this by removing all records in the test method setup.

    It also automatically installs a mock for the random string generation used for
    the state and nonce values, as these need to be stable to properly work together
    with VCR request matching.
    """

    @classmethod
    def setUpTestData(cls):
        OIDCClient.objects.all().delete()
        OIDCProvider.objects.all().delete()

        super().setUpTestData()  # pyright: ignore[reportAttributeAccessIssue]

    def setUp(self):
        super().setUp()  # pyright: ignore[reportAttributeAccessIssue]

        mock_random_state_and_nonce_cm = mock_random_state_and_nonce()
        mock_random_state_and_nonce_cm.__enter__()
        self.addCleanup(  # pyright: ignore[reportAttributeAccessIssue]
            lambda: mock_random_state_and_nonce_cm.__exit__(None, None, None)
        )


@contextmanager
def mock_random_state_and_nonce():
    """Mock the state & nonce random value generation

    Needed so that we get predictable URLs to match with VCR.
    """
    with patch(
        "mozilla_django_oidc.views.get_random_string",
        return_value="not-a-random-string",
    ):
        yield
